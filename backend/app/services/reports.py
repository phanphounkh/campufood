"""Dashboard metrics and sales reports, computed from live database data.

Revenue rules
-------------
* Gross sales  = payments that succeeded (status paid or later refunded), by `paid_at`.
* Refunds      = payments with status refunded, by `refunded_at`.
* Net revenue  = gross sales - refunds.
Pending, failed, expired and cancelled payments never count as revenue.
"""

import csv
import io
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal

from sqlalchemy import ColumnElement, and_, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import bad_request
from app.models import Food, Order, OrderItem, OrderStatus, Payment, PaymentStatus
from app.schemas.admin import (
    DashboardOut,
    KpiValue,
    PopularItem,
    RecentOrder,
    ReportOut,
    ReportPeriod,
    ReportTotals,
    StatusCount,
    TimePoint,
)
from app.services.store_settings import get_store_settings
from app.utils.money import to_money
from app.utils.time import local_day_bounds, local_now, local_tz, parse_hhmm, utcnow

Granularity = Literal["day", "week", "month"]
DashboardRange = Literal["today", "7d", "30d"]

SUCCEEDED = (PaymentStatus.PAID, PaymentStatus.REFUNDED)
FULFILLING = (
    OrderStatus.CONFIRMED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.COMPLETED,
)
ZERO = Decimal("0.00")


def _local(col: ColumnElement) -> ColumnElement:
    """timestamptz -> canteen-local timestamp (no tz), for bucketing."""
    return func.timezone(settings.timezone, col)


def _pct(current: Decimal | int, previous: Decimal | int) -> float | None:
    if not previous:
        return None
    return round(float((Decimal(current) - Decimal(previous)) / Decimal(previous) * 100), 1)


async def _money_sum(session: AsyncSession, *where: ColumnElement) -> Decimal:
    value = await session.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(*where))
    return to_money(value or 0)


async def _period_metrics(session: AsyncSession, start: datetime, end: datetime) -> dict:
    gross = await _money_sum(
        session, Payment.status.in_(SUCCEEDED), Payment.paid_at >= start, Payment.paid_at < end
    )
    refunds = await _money_sum(
        session,
        Payment.status == PaymentStatus.REFUNDED,
        Payment.refunded_at >= start,
        Payment.refunded_at < end,
    )
    paid_orders = await session.scalar(
        select(func.count(distinct(Payment.order_id))).where(
            Payment.status.in_(SUCCEEDED), Payment.paid_at >= start, Payment.paid_at < end
        )
    )
    completed = await session.scalar(
        select(func.count(Order.id)).where(
            Order.status == OrderStatus.COMPLETED, Order.created_at >= start, Order.created_at < end
        )
    )
    paid_orders = int(paid_orders or 0)
    return {
        "orders": paid_orders,
        "gross": gross,
        "refunds": refunds,
        "net": to_money(gross - refunds),
        "completed": int(completed or 0),
        "aov": to_money(gross / paid_orders) if paid_orders else ZERO,
    }


async def _popular_items(
    session: AsyncSession, start: datetime, end: datetime, limit: int
) -> list[PopularItem]:
    """Best sellers among orders whose payment succeeded and was not refunded."""
    paid_order_ids = select(Payment.order_id).where(
        Payment.status == PaymentStatus.PAID, Payment.paid_at >= start, Payment.paid_at < end
    )
    qty = func.sum(OrderItem.quantity).label("qty")
    rows = await session.execute(
        select(
            OrderItem.food_id,
            func.max(OrderItem.food_name_snapshot),
            func.max(OrderItem.food_name_km_snapshot),
            func.max(Food.image_url),
            qty,
            func.sum(OrderItem.line_total),
        )
        .outerjoin(Food, Food.id == OrderItem.food_id)
        .where(OrderItem.order_id.in_(paid_order_ids))
        .group_by(OrderItem.food_id)
        .order_by(qty.desc(), func.max(OrderItem.food_name_snapshot))
        .limit(limit)
    )
    return [
        PopularItem(
            food_id=food_id,
            name_en=name_en,
            name_km=name_km or name_en,
            image_url=image,
            quantity=int(q),
            revenue=to_money(rev),
        )
        for food_id, name_en, name_km, image, q, rev in rows.all()
    ]


async def _revenue_buckets(
    session: AsyncSession, start: datetime, end: datetime, unit: Literal["hour", "day"]
) -> dict[datetime, tuple[int, Decimal]]:
    bucket = func.date_trunc(unit, _local(Payment.paid_at)).label("bucket")
    rows = await session.execute(
        select(bucket, func.count(distinct(Payment.order_id)), func.sum(Payment.amount))
        .where(
            Payment.status == PaymentStatus.PAID, Payment.paid_at >= start, Payment.paid_at < end
        )
        .group_by(bucket)
    )
    return {b: (int(n), to_money(total)) for b, n, total in rows.all()}


async def dashboard(session: AsyncSession, range_: DashboardRange) -> DashboardOut:
    store = await get_store_settings(session)
    tz = local_tz()
    today = local_now().date()
    days = {"today": 1, "7d": 7, "30d": 30}[range_]
    start, _ = local_day_bounds(today - timedelta(days=days - 1))
    _, end = local_day_bounds(today)
    prev_start, prev_end = start - (end - start), start

    cur = await _period_metrics(session, start, end)
    prev = await _period_metrics(session, prev_start, prev_end)

    def kpi(key: str) -> KpiValue:
        return KpiValue(value=cur[key], previous=prev[key], change_pct=_pct(cur[key], prev[key]))

    # Sales over time: hourly within opening hours for "today", daily otherwise.
    sales: list[TimePoint] = []
    if range_ == "today":
        buckets = await _revenue_buckets(session, start, end, "hour")
        first = min(parse_hhmm(store.opening_time).hour, 7)
        last = max(parse_hhmm(store.closing_time).hour, 17)
        for hour in range(first, last + 1):
            naive = datetime.combine(today, datetime.min.time()).replace(hour=hour)
            n, rev = buckets.get(naive, (0, ZERO))
            sales.append(
                TimePoint(
                    label=f"{hour:02d}:00", start=naive.replace(tzinfo=tz), orders=n, revenue=rev
                )
            )

    daily_days = max(days, 7)
    daily_start, _ = local_day_bounds(today - timedelta(days=daily_days - 1))
    daily = await _revenue_buckets(session, daily_start, end, "day")
    daily_points = []
    for i in range(daily_days):
        day = today - timedelta(days=daily_days - 1 - i)
        naive = datetime.combine(day, datetime.min.time())
        n, rev = daily.get(naive, (0, ZERO))
        daily_points.append(
            TimePoint(label=day.isoformat(), start=naive.replace(tzinfo=tz), orders=n, revenue=rev)
        )
    if range_ != "today":
        sales = daily_points[-days:]

    status_rows = await session.execute(
        select(Order.status, func.count(Order.id))
        .where(Order.created_at >= start, Order.created_at < end)
        .group_by(Order.status)
    )
    by_status = dict(status_rows.all())

    live_counts = dict(
        (
            await session.execute(
                select(Order.status, func.count(Order.id))
                .where(
                    Order.status.in_(
                        [
                            OrderStatus.PENDING_PAYMENT,
                            OrderStatus.CONFIRMED,
                            OrderStatus.PREPARING,
                            OrderStatus.READY,
                        ]
                    )
                )
                .group_by(Order.status)
            )
        ).all()
    )

    low_stock = await session.scalar(
        select(func.count(Food.id)).where(
            Food.is_archived.is_(False), Food.stock_quantity <= store.low_stock_threshold
        )
    )

    recent = (await session.scalars(select(Order).order_by(Order.created_at.desc()).limit(8))).all()

    return DashboardOut(
        range=range_,
        generated_at=utcnow(),
        total_orders=kpi("orders"),
        revenue=kpi("net"),
        completed_orders=kpi("completed"),
        average_order_value=kpi("aov"),
        pending_orders=live_counts.get(OrderStatus.CONFIRMED, 0),
        in_progress_orders=live_counts.get(OrderStatus.PREPARING, 0)
        + live_counts.get(OrderStatus.READY, 0),
        awaiting_payment=live_counts.get(OrderStatus.PENDING_PAYMENT, 0),
        low_stock_count=int(low_stock or 0),
        sales_over_time=sales,
        daily_revenue=daily_points,
        orders_by_status=[StatusCount(status=s, count=by_status.get(s, 0)) for s in OrderStatus],
        popular_items=await _popular_items(session, start, end, 5),
        recent_orders=[_recent(o) for o in recent],
    )


def _recent(order: Order) -> RecentOrder:
    payment = order.latest_payment
    return RecentOrder(
        id=order.id,
        order_number=order.order_number,
        customer_name=order.customer_name,
        item_count=sum(i.quantity for i in order.items),
        items_summary=", ".join(f"{i.food_name_snapshot} ×{i.quantity}" for i in order.items),  # noqa: RUF001
        total=order.total,
        payment_status=payment.status if payment else None,
        status=order.status,
        created_at=order.created_at,
    )


# ── Reports ────────────────────────────────────────────────────


def _bucket_start(day: date, granularity: Granularity) -> date:
    if granularity == "week":
        return day - timedelta(days=day.weekday())
    if granularity == "month":
        return day.replace(day=1)
    return day


def _period_label(start: date, granularity: Granularity) -> str:
    if granularity == "week":
        year, week, _ = start.isocalendar()
        return f"{year}-W{week:02d}"
    if granularity == "month":
        return start.strftime("%Y-%m")
    return start.isoformat()


async def report(
    session: AsyncSession, date_from: date, date_to: date, granularity: Granularity
) -> ReportOut:
    if date_to < date_from:
        raise bad_request("INVALID_RANGE", "'to' must be on or after 'from'.")
    if (date_to - date_from).days > 366:
        raise bad_request("INVALID_RANGE", "Reports are limited to one year at a time.")

    start, _ = local_day_bounds(date_from)
    _, end = local_day_bounds(date_to)

    def bucket(col: ColumnElement) -> ColumnElement:
        return func.date(func.date_trunc(granularity, _local(col))).label("bucket")

    periods: dict[date, dict] = {}
    cursor = _bucket_start(date_from, granularity)
    while cursor <= date_to:
        periods[cursor] = defaultdict(lambda: 0)
        if granularity == "day":
            cursor += timedelta(days=1)
        elif granularity == "week":
            cursor += timedelta(days=7)
        else:
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    def add(rows, key: str) -> None:
        for b, value in rows:
            periods.setdefault(b, defaultdict(lambda: 0))[key] += value or 0

    b = bucket(Payment.paid_at)
    succeeded = and_(Payment.status.in_(SUCCEEDED), Payment.paid_at >= start, Payment.paid_at < end)
    add(
        (
            await session.execute(select(b, func.sum(Payment.amount)).where(succeeded).group_by(b))
        ).all(),
        "gross",
    )
    add(
        (
            await session.execute(
                select(b, func.count(distinct(Payment.order_id))).where(succeeded).group_by(b)
            )
        ).all(),
        "orders",
    )

    b = bucket(Payment.refunded_at)
    refunded = and_(
        Payment.status == PaymentStatus.REFUNDED,
        Payment.refunded_at >= start,
        Payment.refunded_at < end,
    )
    add(
        (
            await session.execute(select(b, func.sum(Payment.amount)).where(refunded).group_by(b))
        ).all(),
        "refunds",
    )
    add(
        (
            await session.execute(select(b, func.count(Payment.id)).where(refunded).group_by(b))
        ).all(),
        "refunded_orders",
    )

    b = bucket(Payment.paid_at)
    add(
        (
            await session.execute(
                select(b, func.sum(OrderItem.quantity))
                .join(Payment, Payment.order_id == OrderItem.order_id)
                .where(
                    Payment.status == PaymentStatus.PAID,
                    Payment.paid_at >= start,
                    Payment.paid_at < end,
                )
                .group_by(b)
            )
        ).all(),
        "items",
    )

    b = bucket(Order.created_at)
    add(
        (
            await session.execute(
                select(b, func.count(Order.id))
                .where(
                    Order.status == OrderStatus.CANCELLED,
                    Order.created_at >= start,
                    Order.created_at < end,
                )
                .group_by(b)
            )
        ).all(),
        "cancelled",
    )

    period_rows = []
    for period_start in sorted(periods):
        p = periods[period_start]
        gross, refunds = to_money(p["gross"]), to_money(p["refunds"])
        period_rows.append(
            ReportPeriod(
                period=_period_label(period_start, granularity),
                start=period_start,
                orders=int(p["orders"]),
                items_sold=int(p["items"]),
                gross_sales=gross,
                refunds=refunds,
                net_revenue=to_money(gross - refunds),
                cancelled_orders=int(p["cancelled"]),
            )
        )

    total_orders = sum(p.orders for p in period_rows)
    gross_total = to_money(sum((p.gross_sales for p in period_rows), ZERO))
    refunds_total = to_money(sum((p.refunds for p in period_rows), ZERO))
    totals = ReportTotals(
        orders=total_orders,
        items_sold=sum(p.items_sold for p in period_rows),
        gross_sales=gross_total,
        refunds=refunds_total,
        net_revenue=to_money(gross_total - refunds_total),
        cancelled_orders=sum(p.cancelled_orders for p in period_rows),
        refunded_orders=int(sum(periods[k]["refunded_orders"] for k in periods)),
        average_order_value=to_money(gross_total / total_orders) if total_orders else ZERO,
    )
    return ReportOut(
        date_from=date_from,
        date_to=date_to,
        granularity=granularity,
        totals=totals,
        periods=period_rows,
        best_sellers=await _popular_items(session, start, end, 10),
    )


def report_to_csv(data: ReportOut) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["CampusEats sales report"])
    w.writerow(["From", data.date_from.isoformat(), "To", data.date_to.isoformat()])
    w.writerow(["Granularity", data.granularity])
    w.writerow([])
    w.writerow(
        [
            "Period",
            "Orders",
            "Items sold",
            "Gross sales (USD)",
            "Refunds (USD)",
            "Net revenue (USD)",
            "Cancelled orders",
        ]
    )
    for p in data.periods:
        w.writerow(
            [
                p.period,
                p.orders,
                p.items_sold,
                f"{p.gross_sales:.2f}",
                f"{p.refunds:.2f}",
                f"{p.net_revenue:.2f}",
                p.cancelled_orders,
            ]
        )
    t = data.totals
    w.writerow(
        [
            "TOTAL",
            t.orders,
            t.items_sold,
            f"{t.gross_sales:.2f}",
            f"{t.refunds:.2f}",
            f"{t.net_revenue:.2f}",
            t.cancelled_orders,
        ]
    )
    w.writerow([])
    w.writerow(["Best sellers"])
    w.writerow(["Rank", "Food", "Quantity", "Revenue (USD)"])
    for rank, item in enumerate(data.best_sellers, start=1):
        w.writerow([rank, item.name_en, item.quantity, f"{item.revenue:.2f}"])
    return buf.getvalue()
