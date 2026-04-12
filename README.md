# SWM Auslastung

This script fetches the live utilization data (Auslastung) for Munich public swimming pools and saunas (SWM - Stadtwerke München) and exports it into a CSV file.

## How it works
1. It parses `https://www.swm.de/baeder/auslastung` to find all facility IDs and names.
2. It calls the backend API at `https://counter.ticos-systems.cloud/api/gates/counter` with these IDs.
3. It appends the fetched live data to `auslastung_live.csv`.

## Setup and Usage
Run the python script:

```bash
python3 swm_auslastung.py
```

It will create (or append to) `auslastung_live.csv` with the latest live data.

## Past Data
Currently, there is no public API endpoint known that returns historical data (e.g. `/history` returns 405 Method Not Allowed). The recommended approach to build historical data is to run this script periodically via a cronjob.

Example cronjob to run every 15 minutes:
```
*/15 * * * * /usr/bin/python3 /path/to/swm_auslastung.py
```
