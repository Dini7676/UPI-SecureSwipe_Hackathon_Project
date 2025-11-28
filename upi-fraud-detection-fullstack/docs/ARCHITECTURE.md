# Architecture

## Overview
- Frontend: React + Tailwind, Axios to backend.
- Backend: FastAPI, JWT, Redis (OTP), PostgreSQL (SQLAlchemy).
- ML: LightGBM model training offline; rule-based real-time scoring.
- Deployment: Vercel (frontend), Render (backend), ElephantSQL.

## ASCII Diagram
```
[React UI] --Axios--> [FastAPI]
    |                  |  \__ Redis (OTP)
    |                  |__ PostgreSQL (DB)
    |                  |__ Fraud Engine (Rule/ML)
```

## Data Flow
1. User requests OTP → FastAPI stores OTP in Redis and logs in DB.
2. User verifies OTP → JWT issued, user created if new.
3. Transactions scored → Transaction saved, FraudLog recorded.
4. Dashboards fetch lists and stats.

## Security
- JWT for session; role-based routes can be extended.
- OTP expiry (300s) in Redis.
- CORS configured for frontend origin.
