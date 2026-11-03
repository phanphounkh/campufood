from fastapi import APIRouter, Response, status

from app.api.deps import AdminUser, SessionDep
from app.schemas.catalog import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import catalog

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(session: SessionDep) -> list[CategoryOut]:
    return await catalog.list_categories(session)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, session: SessionDep, _: AdminUser) -> CategoryOut:
    return CategoryOut.model_validate(await catalog.create_category(session, data))


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int, data: CategoryUpdate, session: SessionDep, _: AdminUser
) -> CategoryOut:
    return CategoryOut.model_validate(await catalog.update_category(session, category_id, data))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session: SessionDep, _: AdminUser) -> Response:
    await catalog.delete_category(session, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
