# Database

PostgreSQL 17 runs in Docker. The schema is managed by Alembic (`backend/alembic/versions`).
All timestamps are `timestamptz` stored in UTC. Reports group them by the canteen time zone (`Asia/Phnom_Penh`).
Money is `NUMERIC(10,2)` and is handled as `Decimal` in Python and as integer cents in the browser.

```bash
cd backend
uv run alembic upgrade head                          # apply migrations
uv run alembic revision --autogenerate -m "message"  # after changing models (review the file!)
uv run alembic downgrade -1                          # roll back one step
```

## Tables

| Table | Purpose | Notable constraints |
|---|---|---|
| `users` | Admins, staff and optional customer accounts | `email` unique; `role` ∈ admin/staff/customer (CHECK); Argon2id `password_hash`; `is_active` |
| `categories` | Menu sections (EN/KM names) | `slug` unique; `sort_order` |
| `foods` | Menu items | FK `category_id` (RESTRICT); `price > 0`; `stock_quantity >= 0`; flags `is_available`, `is_featured`, `is_archived` (soft delete) |
| `orders` | One checkout | UUID `id`; `order_number` unique (`CE-` + `order_number_seq`, from 1001); nullable `user_id`; `guest_access_token_hash` unique (SHA-256); `status` CHECK; `subtotal`/`total >= 0`; `cancel_reason` |
| `order_items` | Lines with price/name **snapshots** | `quantity > 0`; unique `(order_id, food_id)`; `food_id` SET NULL on delete |
| `payments` | Payment attempts per order | UUID `id`; `status` ∈ pending/paid/failed/expired/cancelled/refunded; `amount > 0`; `expires_at`, `paid_at`, `refunded_at`; unique `transaction_reference`; **partial unique index: at most one `paid`/`refunded` payment per order** |
| `inventory_movements` | Append-only stock ledger | `quantity_change <> 0`; reason ∈ initial/restock/manual_adjustment/order_reserved/order_released; **partial unique index `(order_id, food_id, reason)` where `order_id` is not null**, so a reservation can be released only once |
| `settings` | Store configuration as key → JSONB value | `key` unique |

Indexes cover the common filters: order status, `created_at`, phone and user; payment status and `paid_at`; the food listing (`is_archived`, `is_available`, `category_id`); and the movement food/order/time columns.

## Lifecycle of stock

```text
order created      foods.stock -= qty   movement(order_reserved, -qty)
payment confirmed  (no change: already reserved)
order cancelled /  foods.stock += qty   movement(order_released, +qty)   ← once only
payment expired
admin restock      foods.stock ± n      movement(restock | manual_adjustment)
```

## Revenue definitions (reports and dashboard)

- **Gross sales**: amounts of payments that succeeded (`paid` or later `refunded`), by `paid_at`.
- **Refunds**: amounts of `refunded` payments, by `refunded_at`.
- **Net revenue**: gross minus refunds.

Pending, failed, expired and cancelled payments never count as revenue.

## Test database

`docker/postgres/init/01-create-test-db.sh` creates `campuseats_test` the first time the volume is initialised. The pytest suite drops and recreates its schema with the real migrations, then truncates all tables between tests. If your volume predates that script, create it once:

```bash
docker compose exec db createdb -U campuseats campuseats_test
```
