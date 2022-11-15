from fastapi import status
from fastapi.responses import JSONResponse, Response

from db import database
from recipes.models import FavoriteCart, Recipe
from settings import NOT_AUTHENTICATED, NOT_FOUND

db_favorite_cart = FavoriteCart(database)
db_recipe = Recipe(database)


async def create_tag_ingredient(db_model, item, user):
    if not user:
        return NOT_AUTHENTICATED
    if user.is_superuser or user.is_staff is True:
        e = await db_model(item)
        if type(e) != int:
            e = str(e).split(": ")[-1]
            return JSONResponse(f"Incorrect {e}", status.HTTP_400_BAD_REQUEST)
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_403_FORBIDDEN)


async def create_cart_favorite(request, pk, user, db_model):
    if not user:
        return NOT_AUTHENTICATED
    recipe = await db_recipe.check_recipe_by_id_author(request, recipe_id=pk)
    if recipe:
        if not await db_favorite_cart.create(pk, user.id, db_model):
            return JSONResponse(
                {"detail": "Already added"}, status.HTTP_400_BAD_REQUEST)
    return recipe or NOT_FOUND


async def delete_cart_favorite(pk, user, db_model):
    if not user:
        return NOT_AUTHENTICATED
    await db_favorite_cart.delete(pk, user.id, db_model)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
