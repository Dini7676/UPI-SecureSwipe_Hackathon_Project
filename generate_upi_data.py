"""
Generate a realistic synthetic UPI transactions CSV with injected fraud patterns.
Output: data/upi_transactions.csv

Usage:
  python scripts/generate_upi_data.py --nrows 1000000 --out data/upi_transactions.csv

Notes:
- Streams non-fraud transactions to CSV to keep memory usage low.
- Builds lightweight per-sender stats while streaming so fraud records can be generated
  based on sender behavior (anomalous amount, new payee, location anomalies, velocity).
- Fraud ratio defaults to 0.5% (~5k frauds for 1M rows).

This script requires: faker, numpy, geopy (for distance) (or we implement haversine inline).
"""
from __future__ import annotations
import argparse
import csv
import math
import random
import uuid
from collections import defaultdict, Counter
from datetime import datetime, timedelta

import numpy as np
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# --- helpers ---

def haversine_km(lat1, lon1, lat2, lon2):
    """Return distance in kilometers between two lat/lon pairs."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def random_point_near(lat, lon, max_km=50):
    """Return a lat/lon within max_km of given point (approximate)."""
    # small random displacement using haversine approximation
    # choose random bearing and distance
    bearing = random.random() * 2 * math.pi
    distance = random.random() * max_km
    R = 6371.0
    lat2 = math.asin(math.sin(math.radians(lat)) * math.cos(distance / R)
                     + math.cos(math.radians(lat)) * math.sin(distance / R) * math.cos(bearing))
    lon2 = math.radians(lon) + math.atan2(math.sin(bearing) * math.sin(distance / R) * math.cos(math.radians(lat)),
                                           math.cos(distance / R) - math.sin(math.radians(lat)) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)


# --- configuration ---
BANKS = ['HDFC', 'SBI', 'ICICI', 'AXIS', 'PAYTM', 'YESBANK', 'KOTAK']
VPADOMAINS = ['okbank', 'upi', 'bank', 'pay']
TRANSACTION_TYPES = ['P2P', 'P2M']


def generate_users(num_users: int):
    """Create a dict of users with home location, primary bank, and typical amount scale."""
    users = {}
    # Rough lat/lon bounding box for India
    min_lat, max_lat = 8.0, 37.0
    min_lon, max_lon = 68.0, 97.0
    for i in range(num_users):
        uname = fake.user_name() + str(random.randint(1, 9999))
        bank = random.choice(BANKS)
        domain = random.choice(VPADOMAINS)
        vpa = f"{uname}@{domain}"
        # Home location somewhere in India
        lat = random.uniform(min_lat, max_lat)
        lon = random.uniform(min_lon, max_lon)
        # Typical transaction amount scale (log-normal mu, sigma)
        # We'll store a typical median amount per user sampled from a broad distribution
        typical_median = float(10 ** random.uniform(math.log10(20), math.log10(2000)))
        users[vpa] = {
            'vpa': vpa,
            'bank': bank,
            'home_lat': lat,
            'home_lon': lon,
            'typical_median': typical_median,
            'preferred_hours': random.choices(range(24), k=6),  # 6 active hours
            'payees': set(),
        }
    return users


def sample_amount(user):
    # Use a log-normal around the user's typical median
    median = user['typical_median']
    # convert median to log-space mu, choose sigma small
    mu = math.log(median)
    sigma = 0.8
    amt = np.random.lognormal(mu, sigma)
    # truncate: min 1, max 200000
    return float(max(1.0, min(amt, 200000.0)))


def random_timestamp(start_dt: datetime, end_dt: datetime):
    delta = end_dt - start_dt
    secs = random.randint(0, int(delta.total_seconds()))
    return start_dt + timedelta(seconds=secs)


# --- main generator ---

def generate_transactions(out_path: str,
                          nrows: int = 1_000_000,
                          fraud_ratio: float = 0.005,
                          num_users: int = 100_000):
    """Stream-generate transactions and write to CSV."
    """
    n_fraud_target = int(nrows * fraud_ratio)
    n_nonfraud = nrows - n_fraud_target

    users = generate_users(num_users)

    # per-sender running stats
    sender_sum = defaultdict(float)
    sender_count = defaultdict(int)
    sender_locations = defaultdict(Counter)
    sender_payees = defaultdict(set)

    start_dt = datetime.utcnow() - timedelta(days=180)  # ~6 months
    end_dt = datetime.utcnow()

    fieldnames = [
        'transaction_id', 'timestamp', 'sender_vpa', 'receiver_vpa', 'amount',
        'sender_bank', 'receiver_bank', 'sender_lat', 'sender_lon', 'transaction_type',
        'device_id', 'is_fraud'
    ]

    print(f"Streaming {n_nonfraud} non-fraud transactions to {out_path} ...")

    with open(out_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Generate non-fraud transactions
        user_keys = list(users.keys())
        num_users_local = len(user_keys)

        for i in range(n_nonfraud):
            # sample sender and receiver
            sender = users[random.randrange(num_users_local)]
            receiver = users[random.randrange(num_users_local)]
            # avoid self-pay
            while receiver['vpa'] == sender['vpa']:
                receiver = users[random.randrange(num_users_local)]

            amount = sample_amount(sender)
            ts = random_timestamp(start_dt, end_dt)
            # sender location near home
            s_lat, s_lon = random_point_near(sender['home_lat'], sender['home_lon'], max_km=50)
            txn = {
                'transaction_id': str(uuid.uuid4()),
                'timestamp': ts.isoformat(),
                'sender_vpa': sender['vpa'],
                'receiver_vpa': receiver['vpa'],
                'amount': round(amount, 2),
                'sender_bank': sender['bank'],
                'receiver_bank': receiver['bank'],
                'sender_lat': round(s_lat, 6),
                'sender_lon': round(s_lon, 6),
                'transaction_type': random.choices(TRANSACTION_TYPES, weights=[0.85, 0.15])[0],
                'device_id': fake.uuid4(),
                'is_fraud': 0,
            }
            writer.writerow(txn)

            # update running stats
            s_vpa = sender['vpa']
            sender_sum[s_vpa] += txn['amount']
            sender_count[s_vpa] += 1
            sender_locations[s_vpa][(round(s_lat, 3), round(s_lon, 3))] += 1
            sender_payees[s_vpa].add(receiver['vpa'])

            if (i + 1) % 100000 == 0:
                print(f"  generated {i+1} / {n_nonfraud} non-fraud txns")

        print("Finished non-fraud streaming. Building sender baselines...")

        # Build baseline stats
        sender_avg = {}
        sender_home = {}
        for vpa in user_keys:
            cnt = sender_count.get(vpa, 0)
            sender_avg[vpa] = (sender_sum[vpa] / cnt) if cnt > 0 else users[vpa]['typical_median']
            # determine most frequent coarse-loc as "home"
            loc_counter = sender_locations.get(vpa)
            if loc_counter and len(loc_counter) > 0:
                most_common_loc, _ = loc_counter.most_common(1)[0]
                sender_home[vpa] = (most_common_loc[0], most_common_loc[1])
            else:
                sender_home[vpa] = (round(users[vpa]['home_lat'], 3), round(users[vpa]['home_lon'], 3))

        # --- Fraud injection ---
        print(f"Injecting {n_fraud_target} fraudulent transactions using multiple patterns...")
        fraud_written = 0

        # prepare sender list that have some history
        active_senders = [v for v in user_keys if sender_count.get(v, 0) >= 3]
        if not active_senders:
            active_senders = user_keys

        # pattern allocation (approximate)
        # HV: 25%, AnomAmt: 25%, TimeAnom: 20%, LocationAnom: 20%, NewPayee: 10%
        remaining = n_fraud_target
        allocations = {
            'hv': int(n_fraud_target * 0.25),
            'anom_amt': int(n_fraud_target * 0.25),
            'time': int(n_fraud_target * 0.2),
            'loc': int(n_fraud_target * 0.2),
            'new_payee': remaining - (int(n_fraud_target * 0.25) + int(n_fraud_target * 0.25) + int(n_fraud_target * 0.2) + int(n_fraud_target * 0.2))
        }

        # 1) High-Velocity Fraud: bursts of small payments in short window
        print(f"  HV frauds: creating {allocations['hv']} events (as bursts)")
        hv_created = 0
        hv_burst_sizes = [5, 10, 20, 30]
        while hv_created < allocations['hv']:
            sender_vpa = random.choice(active_senders)
            # pick or create a new receiver
            receiver_vpa = random.choice(user_keys)
            while receiver_vpa == sender_vpa:
                receiver_vpa = random.choice(user_keys)
            # choose burst size
            burst = random.choice(hv_burst_sizes)
            # pick a start time within last 7 days to simulate velocity
            burst_start = random_timestamp(end_dt - timedelta(days=7), end_dt)
            # small amounts: typically smaller than user's average
            avg = sender_avg.get(sender_vpa, 200.0)
            for j in range(burst):
                if hv_created >= allocations['hv']:
                    break
                ts = burst_start + timedelta(seconds=random.randint(0, 3600))
                amt = max(1.0, round(np.random.lognormal(math.log(max(5, avg*0.05)), 0.5), 2))
                s_home = sender_home.get(sender_vpa)
                s_lat, s_lon = random_point_near(s_home[0], s_home[1], max_km=20)
                txn = {
                    'transaction_id': str(uuid.uuid4()),
                    'timestamp': ts.isoformat(),
                    'sender_vpa': sender_vpa,
                    'receiver_vpa': receiver_vpa,
                    'amount': amt,
                    'sender_bank': users[sender_vpa]['bank'],
                    'receiver_bank': users[receiver_vpa]['bank'],
                    'sender_lat': round(s_lat, 6),
                    'sender_lon': round(s_lon, 6),
                    'transaction_type': 'P2P',
                    'device_id': fake.uuid4(),
                    'is_fraud': 1,
                }
                writer.writerow(txn)
                hv_created += 1
                fraud_written += 1
        print(f"    HV created: {hv_created}")

        # 2) Anomalous Amount: large sudden amounts far above sender average
        print(f"  Anomalous-Amount frauds: {allocations['anom_amt']}")
        anom_created = 0
        while anom_created < allocations['anom_amt']:
            sender_vpa = random.choice(active_senders)
            receiver_vpa = random.choice(user_keys)
            while receiver_vpa == sender_vpa:
                receiver_vpa = random.choice(user_keys)
            avg = sender_avg.get(sender_vpa, 200.0)
            # create large anomaly: 20x - 200x average (but cap)
            factor = random.uniform(20, 200)
            amt = round(min(avg * factor, 500000.0), 2)
            ts = random_timestamp(start_dt, end_dt)
            s_home = sender_home.get(sender_vpa)
            # use usual device but different location sometimes
            s_lat, s_lon = random_point_near(s_home[0], s_home[1], max_km=50)
            txn = {
                'transaction_id': str(uuid.uuid4()),
                'timestamp': ts.isoformat(),
                'sender_vpa': sender_vpa,
                'receiver_vpa': receiver_vpa,
                'amount': amt,
                'sender_bank': users[sender_vpa]['bank'],
                'receiver_bank': users[receiver_vpa]['bank'],
                'sender_lat': round(s_lat, 6),
                'sender_lon': round(s_lon, 6),
                'transaction_type': 'P2P',
                'device_id': fake.uuid4(),
                'is_fraud': 1,
            }
            writer.writerow(txn)
            anom_created += 1
            fraud_written += 1

        # 3) Time Anomaly: large transactions at odd hours (e.g., 3 AM)
        print(f"  Time-anomaly frauds: {allocations['time']}")
        time_created = 0
        while time_created < allocations['time']:
            sender_vpa = random.choice(active_senders)
            receiver_vpa = random.choice(user_keys)
            while receiver_vpa == sender_vpa:
                receiver_vpa = random.choice(user_keys)
            avg = sender_avg.get(sender_vpa, 200.0)
            amt = round(max(avg * random.uniform(5, 100), 1000.0), 2)
            # pick hour in 0-4
            day = random.randint(0, 180)
            ts_base = end_dt - timedelta(days=day)
            ts = ts_base.replace(hour=random.choice([0,1,2,3,4]), minute=random.randint(0,59), second=random.randint(0,59))
            s_home = sender_home.get(sender_vpa)
            s_lat, s_lon = random_point_near(s_home[0], s_home[1], max_km=100)
            txn = {
                'transaction_id': str(uuid.uuid4()),
                'timestamp': ts.isoformat(),
                'sender_vpa': sender_vpa,
                'receiver_vpa': receiver_vpa,
                'amount': amt,
                'sender_bank': users[sender_vpa]['bank'],
                'receiver_bank': users[receiver_vpa]['bank'],
                'sender_lat': round(s_lat, 6),
                'sender_lon': round(s_lon, 6),
                'transaction_type': 'P2P',
                'device_id': fake.uuid4(),
                'is_fraud': 1,
            }
            writer.writerow(txn)
            time_created += 1
            fraud_written += 1

        # 4) Location Anomaly: transaction from far away location relative to sender home
        print(f"  Location-anomaly frauds: {allocations['loc']}")
        loc_created = 0
        while loc_created < allocations['loc']:
            sender_vpa = random.choice(active_senders)
            receiver_vpa = random.choice(user_keys)
            while receiver_vpa == sender_vpa:
                receiver_vpa = random.choice(user_keys)
            avg = sender_avg.get(sender_vpa, 200.0)
            amt = round(max(avg * random.uniform(2, 50), 500.0), 2)
            ts = random_timestamp(start_dt, end_dt)
            s_home = sender_home.get(sender_vpa)
            # generate location far away: 500 - 2500 km
            # pick a random direction and large distance
            distance_km = random.uniform(500, 2500)
            bearing = random.random() * 2 * math.pi
            # approximate new point by shifting lat/lon roughly (not exact but fine)
            new_lat = s_home[0] + (distance_km / 111.0) * math.cos(bearing)
            new_lon = s_home[1] + (distance_km / (111.0 * math.cos(math.radians(s_home[0])))) * math.sin(bearing)
            txn = {
                'transaction_id': str(uuid.uuid4()),
                'timestamp': ts.isoformat(),
                'sender_vpa': sender_vpa,
                'receiver_vpa': receiver_vpa,
                'amount': amt,
                'sender_bank': users[sender_vpa]['bank'],
                'receiver_bank': users[receiver_vpa]['bank'],
                'sender_lat': round(new_lat, 6),
                'sender_lon': round(new_lon, 6),
                'transaction_type': 'P2P',
                'device_id': fake.uuid4(),
                'is_fraud': 1,
            }
            writer.writerow(txn)
            loc_created += 1
            fraud_written += 1

        # 5) New Payee: large first-time payment to a brand-new VPA
        print(f"  New-payee frauds: {allocations['new_payee']}")
        np_created = 0
        while np_created < allocations['new_payee']:
            sender_vpa = random.choice(active_senders)
            # create brand new payee
            new_payee_uname = fake.user_name() + str(uuid.uuid4())[:6]
            new_payee = f"{new_payee_uname}@{random.choice(VPADOMAINS)}"
            amt = round(max(sender_avg.get(sender_vpa, 200.0) * random.uniform(10, 200), 1000.0), 2)
            ts = random_timestamp(start_dt, end_dt)
            s_home = sender_home.get(sender_vpa)
            s_lat, s_lon = random_point_near(s_home[0], s_home[1], max_km=100)
            txn = {
                'transaction_id': str(uuid.uuid4()),
                'timestamp': ts.isoformat(),
                'sender_vpa': sender_vpa,
                'receiver_vpa': new_payee,
                'amount': amt,
                'sender_bank': users[sender_vpa]['bank'],
                'receiver_bank': random.choice(BANKS),
                'sender_lat': round(s_lat, 6),
                'sender_lon': round(s_lon, 6),
                'transaction_type': 'P2P',
                'device_id': fake.uuid4(),
                'is_fraud': 1,
            }
            writer.writerow(txn)
            np_created += 1
            fraud_written += 1

        print(f"Total fraud rows written: {fraud_written} (target {n_fraud_target})")

    print(f"Data generation complete. File written to: {out_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate synthetic UPI transactions CSV with fraud patterns')
    parser.add_argument('--nrows', type=int, default=1000000, help='Total number of transactions to generate')
    parser.add_argument('--out', type=str, default='data/upi_transactions.csv', help='Output CSV path')
    parser.add_argument('--users', type=int, default=100000, help='Number of unique users (VPAs)')
    parser.add_argument('--fraud_ratio', type=float, default=0.005, help='Fraction of transactions to mark as fraud')
    args = parser.parse_args()

    # ensure output dir exists
    import os

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    generate_transactions(args.out, nrows=args.nrows, fraud_ratio=args.fraud_ratio, num_users=args.users)
