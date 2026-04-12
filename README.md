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

## Native Chronos-2 Multivariate Forecasting Compatibility
The exported CSV (`auslastung_live.csv`) is specifically structured to be directly compatible with **Amazon's Chronos-2** foundation model for multivariate time series forecasting.

It provides a lean, long-format DataFrame with the two exact index columns required natively by `Chronos-2`:
1. `item_id`: A unique identifier for each time series (e.g., `südbad_swim`, `südbad_sauna`).
2. `timestamp`: The timestamp of the observation, strictly aligned to 15-minute UTC boundaries.

### Future Forecasting via Serverless API (No Hardware Needed)
If you do not have a powerful GPU or server, you can deploy and query `amazon/chronos-2` using **Hugging Face Serverless Inference Endpoints**.

- The exact URL endpoint to hit is: `https://api-inference.huggingface.co/models/amazon/chronos-2`
- Serverless endpoints scale to zero, meaning **you only pay for the exact seconds the API processes your request** (run on-demand) with absolutely no idle costs.

I have provided a completely concrete, working Python script: `example_forecast.py` which demonstrates exactly how to query this endpoint with the CSV data.

**Run the example:**
```bash
pip install pandas
HUGGINGFACE_TOKEN=your_token_here python3 example_forecast.py
```

Under the hood, `example_forecast.py` reads `auslastung_live.csv`, parses the data into a JSON payload of historical arrays, and queries the URL endpoint. This is exactly the payload format the Serverless API expects for multivariate forecasting:
```json
{
  "inputs": {
      "target": [
          [10, 15, 20, 25, 30, 25, 20],  // person_count history
          [10.0, 15.0, 20.0, 25.0, 30.0] // utilization_percentage history
      ]
  },
  "parameters": {
      "prediction_length": 24, // Forecast 6 hours into the future
      "quantile_levels": [0.1, 0.5, 0.9]
  }
}
```
