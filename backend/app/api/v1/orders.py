import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, GuestToken, OptionalUser, SessionDep, StaffUser
from app.core.rate_limit import rate_limit
from app.models import OrderStatus
from app.repositories.orders import list_orders
from app.schemas.common import Page
from app.schemas.order import (
    OrderCreate,
    OrderCreated,
    OrderOut,
    OrderStatusUpdate,
)
from app.services import orders as order_service
from app.services.payments.service import checkout_out
from app.utils.time import local_day_bounds

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderCreated,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("create_order", 15, 600))],
    summary="Place an order (guest or logged in). Prices are computed server-side.",
)
async def create_order(data: OrderCreate, session: SessionDep, user: OptionalUser) -> OrderCreated:
    order, payment, token = await order_service.create_order(session, data, user)
    return OrderCreated(
        order=OrderOut.model_validate(order),
        payment=checkout_out(order, payment),
        access_token=token,
    )


@router.get("/mine", response_model=Page[OrderOut], summary="Order history of the logged-in user")
async def my_orders(
    session: SessionDep,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> Page[OrderOut]:
    orders, total = await list_orders(session, user_id=user.id, page=page, page_size=page_size)
    return Page(
        items=[OrderOut.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
    )


async def search_orders(
    session: SessionDep,
    _: StaffUser,
    status_filter: Annotated[list[OrderStatus] | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(max_length=80)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[OrderOut]:
    orders, total = await list_orders(
        session,
        statuses=status_filter,
        search=search,
        created_from=local_day_bounds(date_from)[0] if date_from else None,
        created_to=local_day_bounds(date_to)[1] if date_to else None,
        page=page,
        page_size=page_size,
    )
    return Page(
        items=[OrderOut.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
    )


router.add_api_route(
    "",
    search_orders,
    methods=["GET"],
    response_model=Page[OrderOut],
    summary="List and filter orders (staff)",
)


@router.get(
    "/{order_id}",
    response_model=OrderOut,
    summary="Order details (owner, staff, or guest with X-Order-Token)",
)
async def get_order(
    order_id: uuid.UUID, session: SessionDep, user: OptionalUser, token: GuestToken = None
) -> OrderOut:
    order = await order_service.get_accessible_order(session, order_id, user, token)
    if await order_service.expire_if_due(session, order):
        order = await order_service.get_accessible_order(session, order_id, user, token)
    return OrderOut.model_validate(order)


@router.patch("/{order_id}/status", response_model=OrderOut, summary="Advance or cancel (staff)")
async def update_status(
    order_id: uuid.UUID, data: OrderStatusUpdate, session: SessionDep, _: StaffUser
) -> OrderOut:
    order = await order_service.change_status(session, order_id, data.status, data.reason)
    return OrderOut.model_validate(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderOut,
    summary="Customer cancels their own unpaid order",
)
async def cancel_order(
    order_id: uuid.UUID,
    session: SessionDep,
    user: OptionalUser,
    token: GuestToken = None,
) -> OrderOut:
    order = await order_service.cancel_by_customer(session, order_id, user, token)
    return OrderOut.model_validate(order)
