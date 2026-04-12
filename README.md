# SWM Auslastung

This script fetches the live utilization data (Auslastung) for Munich public swimming pools and saunas (SWM - Stadtwerke München) and exports it into a CSV file.

## How it works
1. It parses `https://www.swm.de/baeder/auslastung` to find all facility IDs and names.
2. It calls the backend API at `https://counter.ticos-systems.cloud/api/gates/counter` with these IDs.
3. It validates the data (sanity checks for boundaries/division by zero).
4. It strictly floors the current execution time to the exact 15-minute interval in UTC (`Z`) to prevent duplicate timestamps.
5. It appends the fetched live data to `auslastung_live.csv`.

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

## Native Chronos-2 Multivariate Forecasting Compatibility
The exported CSV (`auslastung_live.csv`) is specifically structured to be directly compatible with **Amazon's Chronos-2** foundation model for multivariate time series forecasting.

It provides a lean, long-format DataFrame with the two exact index columns required natively by `Chronos-2`:
1. `item_id`: A unique identifier for each time series (e.g., `südbad_swim`, `südbad_sauna`).
2. `timestamp`: The timestamp of the observation, strictly aligned to 15-minute UTC boundaries.

### Future Forecasting for Free (via GitHub Actions)
Because the `amazon/chronos-2` model is surprisingly small for a foundation model (only 120M parameters), **it can actually run completely free directly on a standard CPU GitHub Actions runner**!

This repository includes an on-demand forecasting workflow (`.github/workflows/forecast.yml`) which runs the included `example_forecast.py` script.

**To run a multivariate forecast for free:**
1. Navigate to the **Actions** tab in your GitHub repository.
2. Select **Run Chronos-2 Forecast** on the left.
3. Click the **Run workflow** dropdown on the right side.
4. GitHub Actions will boot up a runner, download the model, ingest your historical `auslastung_live.csv`, run a 6-hour multivariate forecast for all pools simultaneously, and commit a new `forecast_results.csv` file back into your repository!

If you wish to run it locally on your own machine instead, simply install the required packages and execute the same script:
```bash
pip install pandas "chronos-forecasting[extras]>=2.2"
python3 example_forecast.py
```
