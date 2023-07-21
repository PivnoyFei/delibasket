from fastapi import APIRouter

from application.auth.views import router as auth_router
from application.recipes import api_recipe
from application.users import api_user

router = APIRouter()

router.include_router(api_recipe.router)
router.include_router(api_user.router)
router.include_router(auth_router, prefix='/auth/token', tags=["auth"])
