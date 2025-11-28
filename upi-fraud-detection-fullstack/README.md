# UPI Fraud Detection Fullstack

Production-style repo with React frontend, FastAPI backend, ML pipeline, PostgreSQL schema, Redis OTP, Docker, and CI.

## Features
- OTP login (mobile/email) with Redis
- JWT sessions with roles (USER/MERCHANT/ADMIN)
- Dashboards: User, Merchant, Admin
- Fraud scoring API (rule-based; ML-ready)
- Transaction and Fraud logs

## Setup

### Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET=changeme
export FRONTEND_ORIGIN=http://localhost:5173
uvicorn app.main:app --reload --app-dir backend
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Set `VITE_API_BASE` to backend URL.

### SQL
Use ElephantSQL for `DATABASE_URL`. Run `sql/tables.sql` and `sql/seed.sql`.

## ML Training
Open `ml/train_model.ipynb` and run to create `ml/model.pkl`.

## Deployment
- Backend: Render. Use Dockerfile in `backend/` or native Python build. Env vars: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `FRONTEND_ORIGIN`.
- Frontend: Vercel. Configure `VITE_API_BASE`.
- Database: ElephantSQL. Import `tables.sql` then `seed.sql`.

## Testing
```bash
pytest -q
```

## Screenshots
- Add UI screenshots here.
