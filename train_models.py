"""
Training script for RandomForest and XGBoost using the engineered features.
Saves best model as `models/xgb_model.joblib` and `models/rf_model.joblib`.

Usage:
  python scripts/train_models.py --in data/upi_features.parquet --out models/
"""
from __future__ import annotations
import argparse
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

import xgboost as xgb
import pandas as pd
from imblearn.over_sampling import SMOTE


FEATURE_COLUMNS = [
    'amount', 'sender_avg_amount', 'amount_deviation', 'sender_trans_count_24h', 'sender_trans_count_1h',
    'is_new_receiver', 'location_deviation_km', 'is_night_transaction', 'hour_of_day', 'day_of_week'
]


def load_data(path: str):
    df = pd.read_parquet(path)
    return df


def prepare_X_y(df: pd.DataFrame):
    df = df.copy()
    df = df.dropna(subset=FEATURE_COLUMNS + ['is_fraud'])
    X = df[FEATURE_COLUMNS]
    y = df['is_fraud']
    return X, y


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='inpath', required=True)
    parser.add_argument('--out', dest='outdir', default='models')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    print(f"Loading features from {args.inpath}...")
    df = load_data(args.inpath)
    X, y = prepare_X_y(df)

    print('Splitting...')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # scale
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # handle imbalance with SMOTE
    print('Applying SMOTE to training set...')
    sm = SMOTE(random_state=42)
    X_res, y_res = sm.fit_resample(X_train_s, y_train)

    # Random Forest
    print('Training RandomForest (class_weight=balanced)...')
    rf = RandomForestClassifier(n_estimators=200, class_weight='balanced', n_jobs=-1, random_state=42)
    rf.fit(X_res, y_res)
    y_pred_rf = rf.predict(X_test_s)
    print('RandomForest classification report:')
    print(classification_report(y_test, y_pred_rf, digits=4))
    joblib.dump({'model': rf, 'scaler': scaler, 'features': FEATURE_COLUMNS}, os.path.join(args.outdir, 'rf_model.joblib'))

    # XGBoost with scale_pos_weight
    print('Training XGBoost...')
    # compute scale_pos_weight
    pos = y_train.sum()
    neg = len(y_train) - pos
    scale_pos_weight = neg / (pos + 1e-9)
    dtrain = xgb.DMatrix(X_res, label=y_res)
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'aucpr',
        'scale_pos_weight': scale_pos_weight,
        'verbosity': 0,
    }
    bst = xgb.train(params, dtrain, num_boost_round=200)
    # wrap into sklearn API for convenience
    xgb_model = xgb.XGBClassifier()
    xgb_model._Booster = bst
    xgb_model._le = None

    # predictions (need scaler)
    y_pred_xgb = (bst.predict(xgb.DMatrix(X_test_s)) > 0.5).astype(int)
    print('XGBoost classification report:')
    print(classification_report(y_test, y_pred_xgb, digits=4))

    joblib.dump({'model': bst, 'scaler': scaler, 'features': FEATURE_COLUMNS}, os.path.join(args.outdir, 'xgb_model.joblib'))

    print('Training complete. Models saved in', args.outdir)
