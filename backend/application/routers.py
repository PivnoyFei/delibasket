from fastapi import APIRouter

from application.auth.views import router as auth_router
from application.ingredients.views import router as ingredient_router
from application.recipes.views import router as recipe_router
from application.tags.views import router as tag_router
from application.users.views import router as user_router

router = APIRouter()
authenticated_router = APIRouter()

router.include_router(user_router, prefix='/users', tags=["users"])
router.include_router(recipe_router, prefix='/recipes', tags=["recipe"])
router.include_router(ingredient_router, prefix='/ingredients', tags=["ingredients"])
router.include_router(tag_router, prefix='/tags', tags=["tags"])
router.include_router(auth_router, prefix='/auth/token', tags=["auth"])
