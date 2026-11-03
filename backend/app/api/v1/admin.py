"""Back-office endpoints. Every route requires a staff or admin session (enforced server-side)."""

import uuid
from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy import Text, case, cast, func, or_, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.exc import IntegrityError

from app.api.deps import AdminUser, SessionDep, StaffUser, require_staff
from app.api.v1.orders import search_orders
from app.core.errors import AppError, conflict, not_found
from app.core.security import hash_password
from app.models import (
    Category,
    Food,
    InventoryMovement,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentStatus,
    User,
    UserRole,
)
from app.repositories.orders import count_by_status, get_order
from app.repositories.users import get_by_email
from app.schemas.admin import (
    AdminPaymentOut,
    CustomerOut,
    DashboardOut,
    InventoryItem,
    InventoryMovementOut,
    InventoryUpdate,
    PaymentSummary,
    ReportOut,
    StoreSettings,
    StoreSettingsUpdate,
    UploadOut,
)
from app.schemas.auth import StaffCreate, UserOut, UserUpdate
from app.schemas.common import Page
from app.schemas.order import OrderOut
from app.services import reports
from app.services.inventory import adjust_stock
from app.services.media import save_food_image
from app.services.store_settings import get_store_settings, update_store_settings
from app.utils.money import to_money
from app.utils.text import escape_like, normalize_phone
from app.utils.time import local_now

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_staff)])

PAID_LIKE = (OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.COMPLETED)


# ── Dashboard & reports ────────────────────────────────────────


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(
    session: SessionDep, range: Literal["today", "7d", "30d"] = "today"
) -> DashboardOut:
    return await reports.dashboard(session, range)


def _default_range(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    today = local_now().date()
    date_to = date_to or today
    return date_from or (date_to - timedelta(days=29)), date_to


@router.get("/reports", response_model=ReportOut)
async def sales_report(
    session: SessionDep,
    date_from: date | None = None,
    date_to: date | None = None,
    granularity: Literal["day", "week", "month"] = "day",
) -> ReportOut:
    start, end = _default_range(date_from, date_to)
    return await reports.report(session, start, end, granularity)


@router.get(
    "/reports/export",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
    summary="Download the sales report as CSV",
)
async def export_report(
    session: SessionDep,
    date_from: date | None = None,
    date_to: date | None = None,
    granularity: Literal["day", "week", "month"] = "day",
) -> Response:
    start, end = _default_range(date_from, date_to)
    data = await reports.report(session, start, end, granularity)
    filename = f"campuseats-sales-{start.isoformat()}-to-{end.isoformat()}.csv"
    return Response(
        content="﻿" + reports.report_to_csv(data),  # BOM so Excel detects UTF-8
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Orders ─────────────────────────────────────────────────────

router.add_api_route(
    "/orders", search_orders, methods=["GET"], response_model=Page[OrderOut], summary="List orders"
)


@router.get("/orders/{order_id}", response_model=OrderOut)
async def order_detail(order_id: uuid.UUID, session: SessionDep) -> OrderOut:
    order = await get_order(session, order_id)
    if order is None:
        raise not_found("Order")
    return OrderOut.model_validate(order)


@router.get("/orders-summary", summary="Order counts per status (for tab badges)")
async def orders_summary(session: SessionDep) -> dict[str, int]:
    counts = await count_by_status(session)
    return {s.value: counts.get(s.value, 0) for s in OrderStatus} | {"all": sum(counts.values())}


# ── Inventory ──────────────────────────────────────────────────


@router.get("/inventory", response_model=list[InventoryItem])
async def inventory(
    session: SessionDep,
    search: Annotated[str | None, Query(max_length=80)] = None,
    low_only: bool = False,
) -> list[InventoryItem]:
    store = await get_store_settings(session)
    reserved = (
        select(OrderItem.food_id, func.sum(OrderItem.quantity).label("qty"))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status == OrderStatus.PENDING_PAYMENT)
        .group_by(OrderItem.food_id)
        .subquery()
    )
    stmt = (
        select(Food, Category.name_en, func.coalesce(reserved.c.qty, 0))
        .join(Category, Category.id == Food.category_id)
        .outerjoin(reserved, reserved.c.food_id == Food.id)
        .where(Food.is_archived.is_(False))
        .order_by(Food.stock_quantity, Food.name_en)
    )
    if search:
        stmt = stmt.where(Food.name_en.ilike(f"%{escape_like(search)}%", escape="\\"))
    if low_only:
        stmt = stmt.where(Food.stock_quantity <= store.low_stock_threshold)
    rows = (await session.execute(stmt)).unique().all()
    return [
        InventoryItem(
            food_id=food.id,
            name_en=food.name_en,
            name_km=food.name_km,
            category_name_en=category_name,
            image_url=food.image_url,
            stock_quantity=food.stock_quantity,
            is_available=food.is_available,
            low_stock=food.stock_quantity <= store.low_stock_threshold,
            reserved_quantity=int(reserved_qty),
            updated_at=food.updated_at,
        )
        for food, category_name, reserved_qty in rows
    ]


@router.patch("/inventory/{food_id}", response_model=InventoryItem)
async def update_inventory(
    food_id: int, data: InventoryUpdate, session: SessionDep, user: StaffUser
) -> InventoryItem:
    food = await adjust_stock(
        session,
        food_id=food_id,
        mode=data.mode,
        quantity=data.quantity,
        reason=data.reason,
        note=data.note,
        user_id=user.id,
        is_available=data.is_available,
    )
    store = await get_store_settings(session)
    return InventoryItem(
        food_id=food.id,
        name_en=food.name_en,
        name_km=food.name_km,
        category_name_en=food.category.name_en,
        image_url=food.image_url,
        stock_quantity=food.stock_quantity,
        is_available=food.is_available,
        low_stock=food.stock_quantity <= store.low_stock_threshold,
        reserved_quantity=0,
        updated_at=food.updated_at,
    )


@router.get("/inventory/movements", response_model=Page[InventoryMovementOut])
async def inventory_movements(
    session: SessionDep,
    food_id: int | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Page[InventoryMovementOut]:
    stmt = (
        select(InventoryMovement, Food.name_en, Order.order_number)
        .join(Food, Food.id == InventoryMovement.food_id)
        .outerjoin(Order, Order.id == InventoryMovement.order_id)
    )
    if food_id is not None:
        stmt = stmt.where(InventoryMovement.food_id == food_id)
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await session.execute(
        stmt.order_by(InventoryMovement.created_at.desc(), InventoryMovement.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        InventoryMovementOut(
            id=m.id,
            food_id=m.food_id,
            food_name_en=name,
            order_id=m.order_id,
            order_number=number,
            quantity_change=m.quantity_change,
            reason=m.reason,
            note=m.note,
            created_at=m.created_at,
        )
        for m, name, number in rows.unique().all()
    ]
    return Page(items=items, total=int(total or 0), page=page, page_size=page_size)


# ── Customers ──────────────────────────────────────────────────


@router.get("/customers", response_model=Page[CustomerOut])
async def customers(
    session: SessionDep,
    search: Annotated[str | None, Query(max_length=80)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[CustomerOut]:
    """Customers aggregated by phone number (guests and registered users alike)."""
    paid = Order.status.in_(PAID_LIKE)
    latest_name = func.array_agg(aggregate_order_by(Order.customer_name, Order.created_at.desc()))
    stmt = (
        select(
            Order.customer_phone,
            latest_name[1].label("name"),
            func.bool_or(Order.user_id.is_not(None)),
            func.max(User.email),
            func.count(Order.id),
            func.count(Order.id).filter(paid),
            func.coalesce(func.sum(Order.total).filter(paid), 0),
            func.min(Order.created_at),
            func.max(Order.created_at).label("last_order_at"),
        )
        .outerjoin(User, User.id == Order.user_id)
        .group_by(Order.customer_phone)
    )
    if search:
        term = search.strip()
        conditions = [Order.customer_name.ilike(f"%{escape_like(term)}%", escape="\\")]
        phone = normalize_phone(term)
        if phone:
            conditions.append(Order.customer_phone.contains(phone))
        stmt = stmt.where(or_(*conditions))
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await session.execute(
        stmt.order_by(func.max(Order.created_at).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        CustomerOut(
            customer_phone=phone,
            customer_name=name,
            is_registered=bool(registered),
            email=email,
            orders_count=count,
            paid_orders=paid_count,
            total_spent=to_money(spent),
            first_order_at=first,
            last_order_at=last,
        )
        for phone, name, registered, email, count, paid_count, spent, first, last in rows.all()
    ]
    return Page(items=items, total=int(total or 0), page=page, page_size=page_size)


# ── Payments ───────────────────────────────────────────────────


@router.get("/payments", response_model=Page[AdminPaymentOut])
async def payments(
    session: SessionDep,
    status_filter: Annotated[PaymentStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(max_length=80)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[AdminPaymentOut]:
    stmt = select(Payment, Order.order_number, Order.customer_name).join(
        Order, Order.id == Payment.order_id
    )
    if status_filter:
        stmt = stmt.where(Payment.status == status_filter)
    if search:
        pattern = f"%{escape_like(search.strip())}%"
        stmt = stmt.where(
            or_(
                Order.order_number.ilike(pattern, escape="\\"),
                Order.customer_name.ilike(pattern, escape="\\"),
                Payment.transaction_reference.ilike(pattern, escape="\\"),
                cast(Payment.id, Text).ilike(pattern, escape="\\"),
            )
        )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await session.execute(
        stmt.order_by(Payment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [
        AdminPaymentOut(
            **{c: getattr(p, c) for c in AdminPaymentOut.model_fields if hasattr(p, c)},
            order_number=number,
            customer_name=name,
        )
        for p, number, name in rows.all()
    ]
    return Page(items=items, total=int(total or 0), page=page, page_size=page_size)


@router.get("/payments/summary", response_model=PaymentSummary)
async def payments_summary(session: SessionDep) -> PaymentSummary:
    rows = (
        await session.execute(
            select(
                Payment.status, func.count(Payment.id), func.coalesce(func.sum(Payment.amount), 0)
            ).group_by(Payment.status)
        )
    ).all()
    by_status = {s.value: (n, amount) for s, n, amount in rows}

    def amount(*statuses: PaymentStatus) -> object:
        return to_money(sum((by_status.get(s.value, (0, 0))[1] for s in statuses), 0))

    return PaymentSummary(
        collected=amount(PaymentStatus.PAID, PaymentStatus.REFUNDED),
        refunded=amount(PaymentStatus.REFUNDED),
        pending=amount(PaymentStatus.PENDING),
        count_by_status={s.value: by_status.get(s.value, (0, 0))[0] for s in PaymentStatus},
    )


# ── Settings, uploads & staff accounts (admin only) ────────────


@router.get("/settings", response_model=StoreSettings)
async def read_settings(session: SessionDep) -> StoreSettings:
    return await get_store_settings(session)


@router.patch("/settings", response_model=StoreSettings)
async def write_settings(
    data: StoreSettingsUpdate, session: SessionDep, _: AdminUser
) -> StoreSettings:
    try:
        return await update_store_settings(session, data)
    except ValidationError as exc:
        details = [
            {
                "field": ".".join(str(p) for p in e["loc"]),
                "message": e["msg"].removeprefix("Value error, "),
            }
            for e in exc.errors()
        ]
        raise AppError(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "VALIDATION_ERROR", "Invalid settings", details
        ) from exc


@router.post(
    "/uploads/images",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a food image (JPEG/PNG/WebP, re-encoded to WebP)",
)
async def upload_image(_: AdminUser, file: Annotated[UploadFile, File()]) -> UploadOut:
    return await save_food_image(file)


@router.get("/users", response_model=list[UserOut])
async def list_staff(session: SessionDep, _: AdminUser) -> list[User]:
    rows = await session.scalars(
        select(User)
        .where(User.role.in_([UserRole.ADMIN, UserRole.STAFF]))
        .order_by(case((User.role == UserRole.ADMIN, 0), else_=1), User.name)
    )
    return list(rows.all())


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_staff(data: StaffCreate, session: SessionDep, _: AdminUser) -> User:
    if await get_by_email(session, data.email):
        raise conflict("EMAIL_TAKEN", "An account with this email already exists.")
    user = User(
        name=data.name,
        email=data.email.lower(),
        phone=normalize_phone(data.phone) if data.phone else None,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise conflict("EMAIL_TAKEN", "An account with this email already exists.") from exc
    await session.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_staff(
    user_id: int, data: UserUpdate, session: SessionDep, admin: AdminUser
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise not_found("User")
    if user.id == admin.id and (data.role not in (None, UserRole.ADMIN) or data.is_active is False):
        raise conflict("SELF_LOCKOUT", "You cannot remove your own admin access.")
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    await session.commit()
    await session.refresh(user)
    return user
