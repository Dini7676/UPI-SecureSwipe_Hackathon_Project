import os
import sys
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

"""
Allow running this file directly (python backend/app/main.py) by
adding the backend folder to sys.path so absolute imports like
`from app.*` work regardless of working directory.
"""
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.auth.routes import router as auth_router
from app.users.routes import router as users_router
from app.merchants.routes import router as merchants_router
from app.admin.routes import router as admin_router
from app.fraud.routes import router as fraud_router
from app.database.db import init_db
from app.database.redis_client import get_redis

app = FastAPI(title="UPI Fraud Detection API", version="1.0.0")

origins = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
    os.getenv("FRONTEND_ORIGIN_ALT", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.add("app.log", rotation="1 MB")
    init_db()
    try:
        r = get_redis()
        r.ping()
        logger.info("Redis connection OK")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled error")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    duration = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time-ms"] = str(duration)
    return response

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "UPI Fraud Detection API. Visit /docs for Swagger UI."}

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(merchants_router, prefix="/merchants", tags=["merchants"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(fraud_router, prefix="/fraud", tags=["fraud"])
