# REST API (`/api/v1`)

Interactive docs: **`/api/docs`** (Swagger UI) and **`/api/redoc`**. The schema is at `/api/openapi.json`.

## Conventions

- **Auth.** `POST /auth/login` sets an `HttpOnly` `ce_session` cookie and a readable `ce_csrf` cookie. Cookie-authenticated `POST`/`PATCH`/`DELETE` requests must send `X-CSRF-Token: <ce_csrf>`. Every write must come from an allowed `Origin`, if one is sent.
- **Guest access.** `POST /orders` returns an `access_token` once. Send it as `X-Order-Token` to read, pay for, or cancel that order.
- **Money.** Exchanged as 2-decimal strings (`"1.50"`, USD).
- **Pagination.** `?page=1&page_size=20` returns `{ "items": [...], "total", "page", "page_size" }`.
- **Errors.** Always `{ "error": { "code", "message", "details" } }`, with codes such as `VALIDATION_ERROR` (422, `details` = `[{field, message}]`), `UNAUTHORIZED` (401), `FORBIDDEN` (403), `NOT_FOUND` (404), `INVALID_TRANSITION`, `ITEMS_UNAVAILABLE`, `PRICE_CHANGED`, `PAYMENT_EXPIRED` (409) and `RATE_LIMITED` (429, with `Retry-After`).

## Endpoints

| Method | Path | Who | Notes |
|---|---|---|---|
| GET | `/health` | public | Liveness + DB check |
| GET | `/settings` | public | Store info, hours, `demo_payments_enabled` |
| POST | `/auth/login` | public | `{email, password, require_staff?}`; rate limited 10/min |
| POST | `/auth/register` | public | Optional customer account; rate limited |
| POST | `/auth/logout` | any | Clears cookies |
| GET | `/auth/me` | logged in | 401 when not logged in |
| GET | `/foods` | public | `category`, `search` (EN/KM), `sort` (`featured`, `price_asc`, `price_desc`, `name`, `newest`), `featured`, `available_only`, `include_archived` (staff) |
| GET | `/foods/{id}` | public | Archived foods are 404 for the public |
| POST · PATCH · DELETE | `/foods`, `/foods/{id}` | admin | DELETE archives (soft delete) |
| GET | `/categories` | public | Includes `food_count` |
| POST · PATCH · DELETE | `/categories`, `/categories/{id}` | admin | 409 `CATEGORY_IN_USE` / `DUPLICATE` |
| POST | `/orders` | guest or customer | Prices recomputed server-side; stock reserved; returns order + pending payment + `access_token`; 15 per 10 min |
| GET | `/orders/mine` | customer | Order history |
| GET | `/orders/{id}` | owner, token holder, staff | 404 otherwise |
| POST | `/orders/{id}/cancel` | owner / token holder | Only while `pending_payment` |
| GET | `/orders` | staff | `status` (repeatable), `search` (number, name, phone), `date_from`, `date_to` |
| PATCH | `/orders/{id}/status` | staff | `{status, reason}`; reason required to cancel; paid orders are refunded on cancel |
| POST | `/payments/demo/create` | owner / token holder | Returns the open payment and its demo QR payload (idempotent) |
| POST | `/payments/demo/confirm` | owner / token holder | Demo mode only; idempotent; payment must belong to the order |
| GET | `/payments/{id}/status` | owner / token holder / staff | |
| GET | `/admin/dashboard` | staff | `range` = `today`, `7d` or `30d` |
| GET | `/admin/reports` | staff | `date_from`, `date_to`, `granularity` (day/week/month) |
| GET | `/admin/reports/export` | staff | CSV download |
| GET | `/admin/orders`, `/admin/orders/{id}`, `/admin/orders-summary` | staff | |
| GET | `/admin/inventory` | staff | `search`, `low_only` |
| PATCH | `/admin/inventory/{food_id}` | staff | `{mode: adjust or set, quantity, reason, note, is_available}` |
| GET | `/admin/inventory/movements` | staff | Stock ledger |
| GET | `/admin/customers` | staff | Aggregated by phone (guests + accounts) |
| GET | `/admin/payments`, `/admin/payments/summary` | staff | |
| GET · PATCH | `/admin/settings` | staff (read) / admin (write) | |
| POST | `/admin/uploads/images` | admin | multipart `file`; JPEG/PNG/WebP ≤ 5 MB → WebP |
| GET · POST · PATCH | `/admin/users`, `/admin/users/{id}` | admin | Staff accounts; you can't remove your own admin access |

## Example: guest checkout

```bash
curl -s -X POST localhost:8000/api/v1/orders -H 'content-type: application/json' -d '{
  "customer_name": "Sokha Chan", "customer_phone": "012 345 678",
  "pickup_time": "2026-11-04T12:00:00+07:00",
  "items": [{"food_id": 1, "quantity": 2}, {"food_id": 13, "quantity": 1}],
  "expected_total": "3.75"
}'
# → 201 {"order": {..., "order_number": "CE-1001", "total": "3.75", "status": "pending_payment"},
#        "payment": {"id": "...", "status": "pending", "qr_payload": "CAMPUSEATS-DEMO|NOT-A-REAL-PAYMENT|..."},
#        "access_token": "..."}
```
