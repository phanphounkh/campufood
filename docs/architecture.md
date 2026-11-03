# Architecture

```text
Browser ──► SvelteKit server (:5173 dev / :3000 prod)
              │  • renders pages (SSR) in the visitor's language (ce_locale cookie)
              │  • hooks.server.ts proxies /api/* and /media/* ──► FastAPI (:8000)
              ▼
           FastAPI ──► PostgreSQL 17 (Docker volume)
              └─ /media (uploaded and seeded food photos, served by StaticFiles)
```

## Why one origin?

The browser only talks to the SvelteKit server. `/api` and `/media` are forwarded to FastAPI by `frontend/src/hooks.server.ts`, the same way in dev and production. So:

- The session cookie is first-party (`HttpOnly`, `SameSite=Lax`, `Secure` in production), with no third-party-cookie or CORS problems.
- Server-side rendering can call the API with the visitor's cookies through SvelteKit's `fetch`.
- The proxy overwrites `X-Forwarded-For` with the real client address, which the API rate limiter uses (`TRUST_PROXY_HEADERS=true`). Never expose the API port directly when that flag is on.

## Backend (`backend/app`)

| Package | Responsibility |
|---|---|
| `core/` | Settings (pydantic-settings), async engine/session, security (Argon2id via pwdlib, JWT, CSRF and guest tokens), error envelope, rate limiter |
| `models/` | SQLAlchemy 2 typed models and enums |
| `schemas/` | Pydantic v2 request/response models. Money serialises as exact strings (`"1.50"`). |
| `repositories/` | Query building (filters, pagination, row locks) |
| `services/` | Business rules: orders, inventory ledger, payments (provider interface + demo KHQR), reports, settings, media |
| `api/` | Routers and dependencies (`OptionalUser`, `StaffUser`, `AdminUser`, `X-Order-Token`) |

### Key rules

- **Server-side pricing.** Order totals come only from `foods.price`, read with `SELECT … FOR UPDATE`. The optional `expected_total` from the client is used only to detect a stale cart (`409 PRICE_CHANGED`).
- **No overselling.** Food rows are locked in id order, stock is checked and decremented in one transaction, and every change is written to `inventory_movements`. A concurrency test fires 8 parallel orders at 3 units of stock: exactly 3 succeed.
- **Stock released exactly once.** Cancellation and expiry release reservations at most once. This is guarded in code and by a partial unique index on `(order_id, food_id, reason)`.
- **Order state machine.** `pending_payment → confirmed → preparing → ready → completed`, and any non-final state can go to `cancelled`. `confirmed` can only be reached through a verified payment. Invalid transitions return `409 INVALID_TRANSITION`.
- **Idempotent payments.** Confirmation locks the order and payment rows. Re-confirming returns the original result. A partial unique index allows at most one successful payment per order.
- **Expiry.** A background task (every 30 s) plus lazy checks on read expire unpaid orders past their payment window, cancel them and release stock.

### Security

- Argon2id password hashing, plus timing equalisation for unknown emails.
- JWT in an `HttpOnly` cookie. The user is re-read from the database on every request, so deactivation and role changes apply immediately.
- CSRF: double-submit token (`ce_csrf` cookie echoed as `X-CSRF-Token`) for cookie-authenticated writes, plus an `Origin` allow-list for every write.
- Guest order access uses a 256-bit random token. Only its SHA-256 hash is stored, and order ids are UUIDs. A missing order and a forbidden order return the same 404.
- Rate limits on login, registration, order creation and payment endpoints (in memory, per process).
- Uploads are decoded with Pillow, size and pixel limited, re-encoded to WebP under a random name, and stripped of metadata.
- Security headers on both servers. `Cache-Control: no-store` on API responses.

## Frontend (`frontend/src`)

| Path | Contents |
|---|---|
| `routes/(client)/` | Student site: home, menu, cart, checkout, `orders/[id]/pay`, `orders/[id]`, orders, about, login, register |
| `routes/admin/` | Admin site with its own layout and a server-side role guard (`+layout.server.ts`) |
| `lib/stores/` | Rune-based stores: cart (integer cents, persisted to `localStorage`, synced across tabs), drag-and-drop, toasts, remembered guest orders |
| `lib/i18n/` | Typed dictionaries (`en.ts`, `km.ts`, `admin.*.ts`). Khmer must cover every English key at compile time. |
| `lib/services/` | Typed API client (CSRF header, error mapping) and per-resource functions |
| `lib/utils/` | Money (cents), pickup slots in canteen time, Zod schemas, formatting |

### Drag and drop

The cart uses a small pointer-events implementation (`lib/stores/dnd.svelte.ts`) instead of HTML5 drag-and-drop or a sortable-list library, because:

- Food is **copied** into the cart, not moved between lists.
- It must work with touch and pen, not just a mouse.
- It needs a custom preview.

With a mouse the whole card is draggable. On touch screens only the grip handle starts a drag, so scrolling still works. Drop targets are the desktop cart panel, the header cart button, and the floating mobile cart. Dragging is never the only way to add food: every card has an **Add** button, and the grip handle is a real button that adds the dish with Enter or Space.

### Internationalisation

The locale lives in the `ce_locale` cookie. The server renders `<html lang>` and the content in that language. Food and category names come from the database in both languages (`name_en` / `name_km`). Elements with Khmer text get `lang="km"`, so they use Noto Sans Khmer with a taller line height that keeps stacked vowels and subscripts from clipping.
