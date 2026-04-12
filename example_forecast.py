import sys
import json
import urllib.request
import os

def run_api_forecast():
    print("Loading data from auslastung_live.csv...")
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas is not installed. Please run `pip install pandas` first.")
        sys.exit(1)

    try:
        df = pd.read_csv("auslastung_live.csv")
    except FileNotFoundError:
        print("Error: auslastung_live.csv not found. Please run swm_auslastung.py first.")
        return

    # Filter data for a specific pool (e.g. Südbad Swim) to forecast
    target_id = "südbad_swim"
    pool_data = df[df["item_id"] == target_id].sort_values("timestamp")

    if len(pool_data) < 10:
        print(f"Warning: Only {len(pool_data)} rows found for {target_id}.")
        print("Chronos-2 requires a history of data to make a forecast.")
        print("We will attempt to send this data anyway to demonstrate the API.\n")

    # Extract the raw timeseries arrays for Multivariate forecasting
    person_count_series = pool_data["person_count"].tolist()
    utilization_series = pool_data["utilization_percentage"].tolist()

    print(f"--- Hugging Face Serverless API Forecast for {target_id} ---")

    token = os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        print("ERROR: HUGGINGFACE_TOKEN environment variable is not set.")
        print("You must create a free access token at https://huggingface.co/settings/tokens")
        print("Usage: HUGGINGFACE_TOKEN=your_token python3 example_forecast.py")
        sys.exit(1)

    # EXACT Hugging Face Serverless Inference API Endpoint for Chronos-2
    api_url = "https://api-inference.huggingface.co/models/amazon/chronos-2"

    # Construct the exact JSON payload
    payload = {
        "inputs": {
            # Provide the multivariate arrays
            "target": [
                person_count_series,
                utilization_series
            ]
        },
        "parameters": {
            "prediction_length": 24, # 24 steps * 15 min = 6 hours into the future
            "quantile_levels": [0.1, 0.5, 0.9] # Output lower bound, median, and upper bound forecasts
        }
    }

    print(f"Sending {len(person_count_series)} historical data points to {api_url}...")

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )

    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode("utf-8"))
        print("\nSUCCESS! Received forecast from Chronos-2:")
        print(json.dumps(result, indent=2))

    except urllib.error.HTTPError as e:
        print(f"\nAPI Request Failed with status code {e.code}")
        print("Response Body:", e.read().decode("utf-8"))
        print("\nNote: The Serverless Inference API might be 'loading' the model if it hasn't been used recently.")
        print("If you receive a 503 (Model is loading), simply wait 20 seconds and try again.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    run_api_forecast()
