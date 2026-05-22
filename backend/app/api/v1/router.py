from fastapi import APIRouter
from app.api.v1 import regions, forecast, alerts, chat

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(regions.router)
api_router.include_router(forecast.router)
api_router.include_router(alerts.router)
api_router.include_router(chat.router)
