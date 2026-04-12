# SWM Auslastung

This script fetches the live utilization data (Auslastung) for Munich public swimming pools and saunas (SWM - Stadtwerke München) and exports it into a CSV file.

## How it works
1. It parses `https://www.swm.de/baeder/auslastung` to find all facility IDs and names.
2. It calls the backend API at `https://counter.ticos-systems.cloud/api/gates/counter` with these IDs.
3. It appends the fetched live data to `auslastung_live.csv`.

## Setup and Usage
Run the python script locally:

```bash
python3 swm_auslastung.py
```

It will create (or append to) `auslastung_live.csv` with the latest live data.

## Collecting Past Data (Free Automated Hosting)
Currently, there is no public API endpoint known that returns historical data (e.g. `/history` returns 405 Method Not Allowed). The recommended approach to build historical data is to run this script periodically.

The absolute **cheapest and easiest way (100% Free)** to collect this data over time is by using **GitHub Actions**.

This repository is already configured with a GitHub Actions workflow (`.github/workflows/scrape.yml`).
Once you push this code to a repository on GitHub:
1. GitHub Actions will automatically run `swm_auslastung.py` every 15 minutes.
2. It will automatically commit the updated `auslastung_live.csv` file back to your repository.
3. Over days, weeks, and months, you will build up a rich, historical CSV file of the "Auslastung" data automatically, without needing to rent a server!

**Note:** Ensure your GitHub repository settings allow Actions to read and write to the repository (Settings -> Actions -> General -> Workflow permissions -> Read and write permissions).
