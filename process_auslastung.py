import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import csv

RAW_FILE = 'auslastung_raw.csv'
LIVE_FILE = 'auslastung_live.csv'

def process():
    if not os.path.exists(RAW_FILE):
        return

    # Load raw data
    df = pd.read_csv(RAW_FILE)
    if df.empty:
        return

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # We want hourly intervals.
    # We find min and max timestamp, floor/ceil to 1 hour
    min_time = df['timestamp'].min().floor('h')
    max_time = df['timestamp'].max().ceil('h')

    # Generate target grid
    target_times = pd.date_range(start=min_time, end=max_time, freq='h')
    # Precompute formatted strings for target times
    target_str_map = {t: t.strftime('%Y-%m-%dT%H:%M:%SZ') for t in target_times}

    output_rows = []

    # Group by item_id to process each time series separately
    for item_id, group in df.groupby('item_id'):
        group = group.sort_values('timestamp')

        for target in target_times:
            # Find the closest observation within [-30m, +30m]
            # Since timestamps might have seconds, we use [-30m, +30m) essentially.
            # We take the absolute difference to find the closest.

            diffs = (group['timestamp'] - target).dt.total_seconds()

            # Filter valid ones: -30 mins (-1800s) to < 30 mins (1800s)
            valid = group[(diffs >= -1800) & (diffs < 1800)]

            if not valid.empty:
                # Find the one with minimum absolute difference
                closest_idx = valid['timestamp'].sub(target).abs().idxmin()
                closest_row = valid.loc[closest_idx]

                # Format exactly as Z UTC
                target_str = target_str_map[target]

                output_rows.append({
                    'timestamp': target_str,
                    'item_id': item_id,
                    'person_count': max(0, int(closest_row['person_count'])),
                    'max_person_count': closest_row['max_person_count'],
                    'utilization_percentage': closest_row['utilization_percentage']
                })

    if not output_rows:
        return

    out_df = pd.DataFrame(output_rows)
    # Sort nicely by timestamp and item
    out_df = out_df.sort_values(['timestamp', 'item_id'])

    out_df.to_csv(LIVE_FILE, index=False)
    print(f"Processed {len(df)} raw rows into {len(out_df)} hourly rows.")

if __name__ == '__main__':
    process()
