import sys
import warnings

warnings.filterwarnings('ignore')

def run_local_forecast():
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas is not installed. Please run `pip install pandas` first.")
        sys.exit(1)

    print("Loading historical data from auslastung_live.csv...")
    try:
        df = pd.read_csv("auslastung_live.csv")
    except FileNotFoundError:
        print("Error: auslastung_live.csv not found. Please run swm_auslastung.py first.")
        sys.exit(1)

    # A forecasting model requires at least some context.
    # Chronos-2 needs sufficient rows per item_id to make a prediction.
    if len(df) < 50:
        print(f"Warning: Only {len(df)} rows found. Time series forecasting requires a healthy history.")
        print("In a real scenario, please wait until the scraper has collected several days of data.")

    try:
        from chronos import ChronosPipeline
    except ImportError:
        print("Error: chronos is not installed in this environment.")
        print("Please run: pip install 'chronos-forecasting>=2.0'")
        sys.exit(1)

    print("Loading amazon/chronos-t5-small model...")
    print("This will download the ~400MB model to the runner if not cached.")
    # Use CPU by default so it runs on GitHub Actions
    pipeline = ChronosPipeline.from_pretrained("amazon/chronos-t5-small", device_map="cpu")

    # Predict the next 24 timesteps (24 * 15 minutes = 6 hours)
    # Target columns: person_count and utilization_percentage
    print("Forecasting the next 6 hours (24 intervals) for all locations simultaneously...")
    pred_df = pipeline.predict_df(
        df,
        prediction_length=24,
        id_column="item_id",
        timestamp_column="timestamp",
        target=["person_count", "utilization_percentage"]
    )

    print("\nForecast completed! Saving to forecast_results.csv...")
    pred_df.to_csv("forecast_results.csv", index=False)
    print("Shape:", pred_df.shape)

    print("\nSample Forecast Output (First 10 Rows):")
    print(pred_df.head(10))

if __name__ == "__main__":
    run_local_forecast()