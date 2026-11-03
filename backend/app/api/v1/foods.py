from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, OptionalUser, SessionDep
from app.core.errors import AppError, not_found
from app.repositories.foods import FoodSort, get_food, list_foods
from app.schemas.catalog import FoodCreate, FoodOut, FoodUpdate
from app.schemas.common import Page
from app.services import catalog

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("", response_model=Page[FoodOut], summary="Browse the menu")
async def get_foods(
    session: SessionDep,
    user: OptionalUser,
    category: Annotated[str | None, Query(max_length=80, description="Category slug")] = None,
    search: Annotated[str | None, Query(max_length=80)] = None,
    sort: FoodSort = "featured",
    featured: bool | None = None,
    available_only: bool = False,
    include_archived: Annotated[bool, Query(description="Staff only")] = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> Page[FoodOut]:
    if include_archived and (user is None or not user.is_staff):
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Staff only")
    foods, total = await list_foods(
        session,
        category=category,
        search=search,
        sort=sort,
        featured=featured,
        available_only=available_only,
        include_archived=include_archived,
        page=page,
        page_size=page_size,
    )
    return Page(
        items=[FoodOut.model_validate(f) for f in foods],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{food_id}", response_model=FoodOut)
async def get_food_detail(food_id: int, session: SessionDep, user: OptionalUser) -> FoodOut:
    food = await get_food(session, food_id)
    if food is None or (food.is_archived and (user is None or not user.is_staff)):
        raise not_found("Food")
    return FoodOut.model_validate(food)


@router.post("", response_model=FoodOut, status_code=status.HTTP_201_CREATED)
async def create_food(data: FoodCreate, session: SessionDep, admin: AdminUser) -> FoodOut:
    return FoodOut.model_validate(await catalog.create_food(session, data, admin.id))


@router.patch("/{food_id}", response_model=FoodOut)
async def update_food(
    food_id: int, data: FoodUpdate, session: SessionDep, admin: AdminUser
) -> FoodOut:
    return FoodOut.model_validate(await catalog.update_food(session, food_id, data, admin.id))


@router.delete(
    "/{food_id}",
    response_model=FoodOut,
    summary="Archive a food (soft delete; keeps order history intact)",
)
async def delete_food(food_id: int, session: SessionDep, _: AdminUser) -> FoodOut:
    return FoodOut.model_validate(await catalog.archive_food(session, food_id))
