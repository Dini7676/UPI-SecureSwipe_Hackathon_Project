# UPI Fraud Detection Fullstack Project Report

## Abstract
This project implements an end-to-end UPI fraud detection system with React frontend, FastAPI backend, SQL database, Redis OTP service, and a hybrid rule/ML scoring engine. It supports OTP login, role-based dashboards, transaction logging, and fraud analytics. The ML pipeline trains a LightGBM classifier on synthetic data to complement rule-based decisions.

## Introduction
Unified Payments Interface (UPI) is widely adopted in India, making fraud detection essential. We designed a modular system focusing on practical deployment, rapid login via OTP, and real-time risk scoring for transactions.

## Objectives
- OTP-based authentication for mobile/email.
- Role-based dashboards (User/Merchant/Admin).
- Real-time fraud scoring API.
- Persist transactions and fraud logs.
- Train ML model with synthetic realistic features.

## System Architecture
See `ARCHITECTURE.md` for overview and diagrams. Components: React UI, FastAPI, PostgreSQL, Redis, Fraud Engine, ML Training.

## Authentication and Authorization
- OTP Service using Redis with 5-minute expiry.
- JWT tokens; roles are `USER`, `MERCHANT`, `ADMIN`.

## Database Schema
Tables: users, merchants, transactions, admin, otp_logs, fraud_logs. See `sql/tables.sql`.

## Fraud Detection Engine
- Rule-based features: amount, channel, category, bursts.
- Hybrid approach: rules provide initial score; ML provides refined probability (future work with `model.pkl`).
- Risk levels: LOW (<0.4), MEDIUM (0.4–0.75), HIGH (>=0.75).

## ML Pipeline
Synthetic generator defines latent fraud patterns; feature engineering builds numerical features; LightGBM trained in `train_model.ipynb`.

## Frontend UI
- Login via OTP; token persisted.
- User Dashboard: transaction history.
- Merchant Dashboard: QR generator and transactions.
- Admin Panel: stats and fraud logs.

## API Design
Endpoints documented in `docs/API.md`.

## Deployment Strategy
- Backend Docker image; deploy to Render with `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `FRONTEND_ORIGIN`.
- Frontend deploy to Vercel; set `VITE_API_BASE` env.
- Database via ElephantSQL; run `tables.sql` and `seed.sql`.

## Testing
- Pytest for API health and fraud scoring basics.

## Future Work
- Integrate ML `model.pkl` in API for blended scoring.
- Expand role-based protection and audit trails.
- Add real QR rendering and charts.

## Conclusion
This production-style repository demonstrates a complete, deployable UPI fraud detection stack with extensible components and clear docs.
