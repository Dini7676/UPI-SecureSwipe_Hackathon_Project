"""
Exploratory Data Analysis for the synthetic UPI transactions dataset.

Usage:
  python scripts/eda.py --in data/upi_transactions.csv --out results/

Generates:
 - class imbalance summary (printed)
 - amount distribution plots (hist + log scale)
 - transactions by hour/day (fraud vs non-fraud)
 - confusion-free map of fraud locations saved as HTML (folium)
 - saves plots to --out directory
"""
from __future__ import annotations
import argparse
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set(style='whitegrid')


def load_data(path: str, nrows: int | None = None):
    print(f"Loading data from {path}...")
    df = pd.read_csv(path, nrows=nrows, parse_dates=['timestamp'])
    return df


def class_imbalance(df: pd.DataFrame):
    total = len(df)
    fraud = df['is_fraud'].sum()
    pct = fraud / total * 100
    print(f"Total rows: {total}")
    print(f"Fraudulent rows: {fraud} ({pct:.4f}%)")
    return total, fraud, pct


def plot_amount_distribution(df: pd.DataFrame, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    plt.figure(figsize=(10, 5))
    sns.histplot(df['amount'], bins=200, log_scale=(False, True))
    plt.title('Transaction amount distribution (log y scale)')
    plt.xlabel('Amount (INR)')
    plt.savefig(os.path.join(out_dir, 'amount_distribution_logy.png'))
    plt.close()

    plt.figure(figsize=(10, 5))
    sns.histplot(df[df['is_fraud'] == 0]['amount'], bins=200, color='C0', label='non-fraud', alpha=0.6)
    sns.histplot(df[df['is_fraud'] == 1]['amount'], bins=200, color='C3', label='fraud', alpha=0.6)
    plt.xscale('log')
    plt.legend()
    plt.title('Amount distribution: fraud vs non-fraud (log x scale)')
    plt.savefig(os.path.join(out_dir, 'amount_distribution_fraud_vs_nonfraud_logx.png'))
    plt.close()


def time_based_plots(df: pd.DataFrame, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    df['hour'] = df['timestamp'].dt.hour
    df['dayofweek'] = df['timestamp'].dt.dayofweek

    plt.figure(figsize=(10, 5))
    sns.countplot(x='hour', data=df, order=list(range(24)))
    plt.title('Transactions by hour (all)')
    plt.savefig(os.path.join(out_dir, 'tx_by_hour_all.png'))
    plt.close()

    plt.figure(figsize=(10, 5))
    sns.countplot(x='hour', data=df[df['is_fraud'] == 1], order=list(range(24)))
    plt.title('Transactions by hour (fraud only)')
    plt.savefig(os.path.join(out_dir, 'tx_by_hour_fraud.png'))
    plt.close()

    plt.figure(figsize=(10, 5))
    sns.countplot(x='dayofweek', data=df, order=list(range(7)))
    plt.title('Transactions by day of week (0=Mon)')
    plt.savefig(os.path.join(out_dir, 'tx_by_day_all.png'))
    plt.close()

    plt.figure(figsize=(10, 5))
    sns.countplot(x='dayofweek', data=df[df['is_fraud'] == 1], order=list(range(7)))
    plt.title('Transactions by day of week (fraud only)')
    plt.savefig(os.path.join(out_dir, 'tx_by_day_fraud.png'))
    plt.close()


def fraud_locations_map(df: pd.DataFrame, out_dir: str):
    try:
        import folium
    except Exception:
        print('folium not installed; skipping map generation')
        return
    os.makedirs(out_dir, exist_ok=True)
    frauds = df[df['is_fraud'] == 1]
    if frauds.empty:
        print('No frauds to map')
        return
    # center map over mean coords
    center_lat = frauds['sender_lat'].mean()
    center_lon = frauds['sender_lon'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
    for _, r in frauds.iterrows():
        folium.CircleMarker(location=[r['sender_lat'], r['sender_lon']], radius=3, color='red', fill=True, fill_opacity=0.7).add_to(m)
    out_path = os.path.join(out_dir, 'fraud_locations.html')
    m.save(out_path)
    print(f'Wrote fraud locations map to {out_path}')


def sample_frauds(df: pd.DataFrame, n: int = 10):
    print('Sample fraud rows:')
    print(df[df['is_fraud'] == 1].sample(n=min(n, df['is_fraud'].sum())).to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='infile', required=True, help='Input CSV file')
    parser.add_argument('--out', dest='outdir', default='results', help='Output directory for plots')
    parser.add_argument('--nrows', type=int, default=None, help='Read only nrows (useful for testing)')
    args = parser.parse_args()

    df = load_data(args.infile, nrows=args.nrows)
    class_imbalance(df)
    plot_amount_distribution(df, args.outdir)
    time_based_plots(df, args.outdir)
    fraud_locations_map(df, args.outdir)
    sample_frauds(df, n=10)
