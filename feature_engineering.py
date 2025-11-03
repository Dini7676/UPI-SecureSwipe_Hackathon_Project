"""
Feature engineering for Suraksha project.
Reads `data/upi_transactions.csv` (or --in), computes features described in Phase 3, and writes
`data/upi_features.parquet` and `models/sender_baselines.json` used by the API.

Usage:
  python scripts/feature_engineering.py --in data/upi_transactions.csv --out data/upi_features.parquet

Notes:
- For large CSVs, use --nrows to limit rows during development.
- This script loads the full CSV into memory. If your data is too large, we can adapt to
  a chunked approach and use a small feature store (Redis/Postgres) for baselines.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from collections import Counter

import numpy as np
import pandas as pd


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def compute_sender_baselines(df: pd.DataFrame):
    """Compute per-sender baseline info: avg amount, home location (mode of rounded coords), known_payees set"""
    baselines = {}
    grouped = df.groupby('sender_vpa')
    for sender, g in grouped:
        avg_amount = float(g['amount'].mean()) if len(g) > 0 else 0.0
        # determine most frequent coarse location
        coords = list(zip(g['sender_lat'].round(3), g['sender_lon'].round(3)))
        if coords:
            most_common = Counter(coords).most_common(1)[0][0]
            home_lat, home_lon = float(most_common[0]), float(most_common[1])
        else:
            home_lat, home_lon = float(g['sender_lat'].mean()), float(g['sender_lon'].mean())
        payees = list(g['receiver_vpa'].unique())
        baselines[sender] = {
            'avg_amount': avg_amount,
            'home_lat': home_lat,
            'home_lon': home_lon,
            'known_payees': payees,
        }
    return baselines


def create_features(df: pd.DataFrame, baselines: dict):
    df = df.copy()
    # parse timestamp already done by read_csv if parse_dates used
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_night_transaction'] = df['hour_of_day'].isin([0, 1, 2, 3, 4]).astype(int)

    # sender baseline features
    df['sender_avg_amount'] = df['sender_vpa'].map(lambda x: baselines.get(x, {}).get('avg_amount', np.nan))
    # amount deviation
    df['amount_deviation'] = (df['amount'] - df['sender_avg_amount']) / (df['sender_avg_amount'] + 1e-9)

    # is_new_receiver
    df['is_new_receiver'] = df.apply(lambda r: 0 if r['receiver_vpa'] in baselines.get(r['sender_vpa'], {}).get('known_payees', []) else 1, axis=1)

    # location deviation (km)
    df['sender_home_lat'] = df['sender_vpa'].map(lambda x: baselines.get(x, {}).get('home_lat', np.nan))
    df['sender_home_lon'] = df['sender_vpa'].map(lambda x: baselines.get(x, {}).get('home_lon', np.nan))
    df['location_deviation_km'] = haversine_km(df['sender_home_lat'].astype(float), df['sender_home_lon'].astype(float), df['sender_lat'].astype(float), df['sender_lon'].astype(float))

    # behavioral aggregations: counts in last 24h and 1h (approximate using groupby and rolling with time)
    df = df.sort_values('timestamp')
    df.set_index('timestamp', inplace=True)

    # compute per-sender rolling counts
    df['sender_trans_count_24h'] = df.groupby('sender_vpa')['transaction_id'].rolling('24h').count().reset_index(level=0, drop=True)
    df['sender_trans_count_1h'] = df.groupby('sender_vpa')['transaction_id'].rolling('1h').count().reset_index(level=0, drop=True)

    # reset index
    df.reset_index(inplace=True)

    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='infile', required=True, help='Input CSV')
    parser.add_argument('--out', dest='outpath', default='data/upi_features.parquet', help='Output parquet path')
    parser.add_argument('--nrows', type=int, default=None, help='Read only nrows (useful for dev)')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.outpath), exist_ok=True)

    print(f"Loading data from {args.infile} ...")
    df = pd.read_csv(args.infile, nrows=args.nrows, parse_dates=['timestamp'])
    print(f"Loaded {len(df)} rows")

    print("Computing sender baselines...")
    baselines = compute_sender_baselines(df)

    print(f"Creating features on {len(df)} rows...")
    df_feat = create_features(df, baselines)

    print(f"Saving features to {args.outpath} ...")
    df_feat.to_parquet(args.outpath, index=False)

    # save baselines for API
    os.makedirs('models', exist_ok=True)
    with open('models/sender_baselines.json', 'w') as f:
        json.dump(baselines, f)

    print('Feature engineering complete.')
