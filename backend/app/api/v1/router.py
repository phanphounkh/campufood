from fastapi import APIRouter

from app.api.v1 import admin, auth, categories, foods, orders, payments, store

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(store.router)
api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(foods.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(admin.router)
