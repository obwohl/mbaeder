import urllib.request
import json
import csv
import re
from datetime import datetime
import os

def get_auslastung():
    # 1. Fetch HTML to find IDs and Names
    url_html = "https://www.swm.de/baeder/auslastung"
    req_html = urllib.request.Request(url_html, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req_html).read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching HTML: {e}")
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
        api_response = urllib.request.urlopen(req_api).read().decode('utf-8')
        data = json.loads(api_response)
    except Exception as e:
        print(f"Error fetching API: {e}")
        return

    # 3. Write to CSV
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    csv_filename = "auslastung_live.csv"

    # Check if we should write headers
    write_header = not os.path.exists(csv_filename)

    with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(['Timestamp', 'Organization_ID', 'Location_Name', 'Type', 'Person_Count', 'Max_Person_Count', 'Utilization_Percentage'])

        for item in data:
            org_id = str(item.get('organizationUnitId'))
            p_count = item.get('personCount')
            m_count = item.get('maxPersonCount')
            loc = locations.get(org_id, {'name': 'Unknown', 'type': 'Unknown'})

            utilization = round((p_count / m_count) * 100, 1) if m_count and m_count > 0 else 0

            writer.writerow([timestamp, org_id, loc['name'], loc['type'], p_count, m_count, utilization])

    print(f"Successfully wrote {len(data)} records to {csv_filename}")

if __name__ == "__main__":
    get_auslastung()
