from fastapi import APIRouter
from app.api.vessels import router as vessels_router

api_router = APIRouter()
api_router.include_router(vessels_router, prefix="/vessels", tags=["vessels"])
