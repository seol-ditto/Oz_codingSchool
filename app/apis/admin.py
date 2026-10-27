from fastapi import APIRouter

from app.apis.dependencies import AdminUser, DBSession


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])