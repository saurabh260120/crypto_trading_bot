"""
API v1 router.
"""
from fastapi import APIRouter
from app.api.v1 import auth, profiles, algorithms, orders, metrics, logs

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(algorithms.router, prefix="/algorithms", tags=["algorithms"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])

