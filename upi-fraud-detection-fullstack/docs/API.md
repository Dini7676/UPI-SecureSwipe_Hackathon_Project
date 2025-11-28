# API Documentation

Base URL: `http://localhost:8000`

## Auth
- `POST /auth/send-otp` — body: `{ mobile, email? }` → `{ message, otp_debug }`
- `POST /auth/verify-otp` — body: `{ mobile, email?, otp }` → `{ access_token, role }`

## Users
- `GET /users/` → list users
- `GET /users/{id}` → user detail
- `PUT /users/{id}` → update `{ name?, email? }`
- `GET /users/{id}/transactions` → user transactions

## Merchants
- `GET /merchants/` → list merchants
- `POST /merchants/` → create merchant `{ name, upi_id, category? }`
- `GET /merchants/{id}/transactions` → merchant transactions

## Admin
- `GET /admin/stats` → basic system stats
- `GET /admin/fraud-logs` → latest fraud logs

## Fraud
- `POST /fraud/score` — body: `{ user_id, merchant_id, amount, channel, merchant_category, user_tx_last_hour, merchant_tx_last_hour }` → `{ transaction_id, risk_score, level }`

Auth: Send `Authorization: Bearer <token>` for protected routes (extend as needed).
