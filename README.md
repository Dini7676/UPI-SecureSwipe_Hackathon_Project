# Suraksha: A Real-Time ML System for UPI Fraud Detection

## Abstract
Suraksha is an end-to-end project that demonstrates building a real-time fraud detection system for UPI transactions using synthetic data. It includes data generation, EDA, feature engineering, model training, and a FastAPI deployment for real-time inference.

## Repo structure
- `data/` - datasets (CSV & parquet)
- `scripts/` - data generation, EDA, feature engineering, training
- `models/` - saved models and baseline artifacts
- `api/` - FastAPI application

## Quickstart
1. Create virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Generate synthetic data (example, 100k for quick iteration):

```bash
python scripts/generate_upi_data.py --nrows 100000 --out data/upi_transactions.csv --users 20000
```

3. Run EDA:

```bash
python scripts/eda.py --in data/upi_transactions.csv --out results --nrows 100000
```

4. Feature engineering:

```bash
python scripts/feature_engineering.py --in data/upi_transactions.csv --out data/upi_features.parquet --nrows 100000
```

5. Train models:

```bash
python scripts/train_models.py --in data/upi_features.parquet --out models
```

6. Start API:

```bash
uvicorn api.main:app --reload --port 8000
```

## Architecture
See `docs/architecture.md` for a detailed streaming design (Kafka -> Stream Processor -> Model API -> Decisioning + Alerts)

## Future work
- Use a feature store (Redis/Postgres) for per-sender state
- Deploy with Kubernetes, autoscaling, and monitoring
- Experiment with sequence models for user behavior
