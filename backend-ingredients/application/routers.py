from fastapi import APIRouter

from application.ingredients.views import router as ingredient_router

router = APIRouter()
router.include_router(ingredient_router, prefix="/ingredients", tags=["ingredients"])
