"""
FastAPI service for Suraksha: loads saved model and sender baselines, re-computes features for a single transaction,
and returns fraud prediction and score.

Usage:
  uvicorn api.main:app --reload --port 8000

Endpoints:
 - GET /health
 - POST /predict
"""
from __future__ import annotations
import json
import math
from typing import Dict

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# load models and baselines
MODEL_PATH = 'models/xgb_model.joblib'
BASELINES_PATH = 'models/sender_baselines.json'

print('Loading model and baselines...')
model_bundle = joblib.load(MODEL_PATH) if 'xgb_model.joblib' else None
# model_bundle may contain different shapes depending on how saved; we expect {'model': booster, 'scaler': scaler, 'features': [...]} 
try:
    with open(BASELINES_PATH) as f:
        baselines = json.load(f)
except Exception:
    baselines = {}

FEATURES = model_bundle.get('features') if isinstance(model_bundle, dict) else []


class TransactionIn(BaseModel):
    transaction_id: str
    timestamp: str
    sender_vpa: str
    receiver_vpa: str
    amount: float
    sender_bank: str
    receiver_bank: str
    sender_lat: float
    sender_lon: float
    transaction_type: str
    device_id: str


@app.get('/health')
async def health():
    return {'status': 'ok'}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@app.post('/predict')
async def predict(tx: TransactionIn):
    # reconstruct a one-row df
    row = tx.dict()
    # compute features
    sender = row['sender_vpa']
    baseline = baselines.get(sender, {})
    sender_avg = baseline.get('avg_amount', np.nan)
    amount_deviation = (row['amount'] - sender_avg) / (sender_avg + 1e-9)
    is_new_receiver = 0 if row['receiver_vpa'] in baseline.get('known_payees', []) else 1
    # location deviation
    home_lat = baseline.get('home_lat')
    home_lon = baseline.get('home_lon')
    location_deviation_km = haversine_km(home_lat, home_lon, row['sender_lat'], row['sender_lon']) if home_lat and home_lon else 0.0
    # time features
    ts = pd.to_datetime(row['timestamp'])
    hour_of_day = ts.hour
    day_of_week = ts.dayofweek
    is_night_transaction = 1 if hour_of_day in [0,1,2,3,4] else 0

    feat_vec = [
        row['amount'], sender_avg, amount_deviation, 0, 0,
        is_new_receiver, location_deviation_km, is_night_transaction, hour_of_day, day_of_week
    ]

    # scale using scaler
    scaler = model_bundle.get('scaler') if isinstance(model_bundle, dict) else None
    if scaler is not None:
        Xs = scaler.transform([feat_vec])
    else:
        Xs = np.array([feat_vec])

    # predict with xgboost booster
    bst = model_bundle.get('model') if isinstance(model_bundle, dict) else None
    if bst is None:
        return {'transaction_id': tx.transaction_id, 'is_fraud': 0, 'fraud_score': 0.0, 'error': 'no model loaded'}

    try:
        prob = bst.predict(xgb.DMatrix(Xs)) if hasattr(bst, 'predict') else bst.predict(xgb.DMatrix(Xs))
        score = float(prob[0]) if hasattr(prob, '__len__') else float(prob)
    except Exception:
        # try sklearn wrapper
        try:
            score = float(bst.predict_proba(Xs)[:, 1][0])
        except Exception:
            score = 0.0

    is_fraud = int(score > 0.5)
    return {'transaction_id': tx.transaction_id, 'is_fraud': is_fraud, 'fraud_score': score}
