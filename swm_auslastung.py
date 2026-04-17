import urllib.request
import json
import csv
import re
from datetime import datetime, timezone, timedelta
import os
import logging
import urllib.error

# Setup logging to both console and a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

def get_auslastung():
    # 1. Fetch HTML to find IDs and Names
    url_html = "https://www.swm.de/baeder/auslastung"
    req_html = urllib.request.Request(url_html, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req_html).read().decode('utf-8')
    except Exception as e:
        logging.error(f"Error fetching HTML: {e}")
        return

    # Extract location details using regex
    blocks = re.split(r'<bath-capacity-item', html)[1:]
    locations = {}
    for block in blocks:
        icon_match = re.search(r'icon-name="([^"]+)"', block)
        name_match = re.search(r'bath-name="([^"]+)"', block)
        id_match = re.search(r'organization-unit-id="([^"]+)"', block)

        if icon_match and name_match and id_match:
            b_type = icon_match.group(1)
            b_name = name_match.group(1)
            b_id = id_match.group(1)
            locations[b_id] = {'name': b_name, 'type': b_type}

    # 2. Fetch live data from Ticos API
    ids_str = ",".join(locations.keys())
    api_url = f"https://counter.ticos-systems.cloud/api/gates/counter?organizationUnitIds={ids_str}"
    req_api = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        response = urllib.request.urlopen(req_api)
        logging.info(f"API response status: {response.getcode()}")
        api_response = response.read().decode('utf-8')
        logging.info(f"API response body length: {len(api_response)}")
        logging.info(f"API response body snippet: {api_response[:100]}...")
        data = json.loads(api_response)
    except urllib.error.HTTPError as e:
        logging.error(f"HTTPError fetching API: {e.code} - {e.reason}")
        logging.error(f"Error headers: {e.headers}")
        logging.error(f"Error body: {e.read().decode('utf-8')}")
        return
    except Exception as e:
        logging.error(f"Error fetching API: {e}")
        return



    # 3. Process and write to CSV
    now = datetime.now(timezone.utc)
    # Use exact timestamp
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    csv_filename = "auslastung_raw.csv"

    # Check if we should write headers
    write_header = not os.path.exists(csv_filename)

    with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(['timestamp', 'item_id', 'person_count', 'max_person_count', 'utilization_percentage'])

        written_count = 0
        for item in data:

            org_id = str(item.get('organizationUnitId'))
            p_count = item.get('personCount')
            m_count = item.get('maxPersonCount')

            # Sanity checks
            if not isinstance(p_count, (int, float)) or p_count < 0:
                continue
            if not isinstance(m_count, (int, float)) or m_count <= 0:
                continue

            loc = locations.get(org_id, {'name': 'Unknown', 'type': 'Unknown'})
            if loc['name'] == 'Unknown':
                continue

            utilization = round((p_count / m_count) * 100, 1)

            item_id = f"{loc['name']}_{loc['type']}".replace(' ', '_').lower()

            writer.writerow([timestamp, item_id, p_count, m_count, utilization])
            written_count += 1

    logging.info(f"Successfully wrote {written_count} records to {csv_filename}")


if __name__ == "__main__":
    get_auslastung()
