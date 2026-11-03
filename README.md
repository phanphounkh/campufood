# CampusEats — Student Food Ordering Platform

CampusEats is a bilingual (English / ខ្មែរ) food-ordering web app for a Cambodian student canteen.

- **Students** browse the menu. They drag dishes into a cart (or tap **+**), check out as a guest, pay with a **demo KHQR** flow, and track their order live.
- **Staff and admins** run the kitchen from `/admin`: orders, menu, categories, inventory, customers, payments, reports and settings.

> **Payments are a demo.** No real money moves. The QR code holds non-payable demo text, and
> "Simulate Payment" only works when `DEMO_PAYMENTS_ENABLED=true` outside production.
> See [docs/payment-demo.md](docs/payment-demo.md).

| Layer | Stack |
|---|---|
| Web | SvelteKit 3 · Svelte 5 (runes) · TypeScript · Tailwind CSS 4 · Lucide · Zod |
| API | Python 3.12+ · FastAPI · Pydantic v2 · SQLAlchemy 2 (async) · Alembic · psycopg 3 · uv |
| Data | PostgreSQL 17 in Docker (persistent volume, health check) |
| Tests | pytest + HTTPX (real Postgres) · Vitest (unit + browser components) · Playwright (E2E) |

---

## 1. Requirements

- Docker with Docker Compose v2
- Python **3.12+** and [uv](https://docs.astral.sh/uv/)
- Node.js **22+** and npm
- (E2E tests only) Playwright Chromium: `cd frontend && npm run test:e2e:install`

## 2. Configure

```bash
cp .env.example .env
```

Then edit `.env`:

| Variable | What it does |
|---|---|
| `POSTGRES_PASSWORD` | Database password. Generate one with `openssl rand -hex 24`. Use the same value inside `DATABASE_URL` and `TEST_DATABASE_URL`. |
| `JWT_SECRET` | Signs session tokens. Generate with `openssl rand -hex 32`. The API refuses weak values in production. |
| `DEMO_PAYMENTS_ENABLED` | Enables the "Simulate Payment" endpoint. It is always disabled when `APP_ENV=production`. |
| `ALLOWED_ORIGINS` | Browser origins allowed to make state-changing requests (Origin check + CORS). |
| `COOKIE_SECURE` | `true` behind HTTPS. Required in production. |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | The first admin account, created by the seed script. Leave the password empty to get a random one printed **once**. |
| `API_INTERNAL_URL` | Where the SvelteKit server forwards `/api` and `/media`. Default `http://127.0.0.1:8000`. |

Every variable is documented in [.env.example](.env.example).

## 3. Run locally (recommended for development)

PostgreSQL runs in Docker. The API and web app run on your machine.

```bash
# 1) Database (also creates the campuseats_test database for the test suite)
docker compose up -d db

# 2) API: install, migrate, seed, serve on http://127.0.0.1:8000
cd backend
uv sync
uv run alembic upgrade head
uv run python scripts/seed.py --demo-orders   # menu + settings + admin (+ 30 days of sample orders)
uv run uvicorn app.main:app --reload --port 8000

# 3) Web app on http://localhost:5173 (new terminal)
cd frontend
npm install
npm run dev
```

The backend and the web app both read the repo-level `.env`.

| URL | What |
|---|---|
| http://localhost:5173 | Student site |
| http://localhost:5173/admin | Admin site (log in with the seeded admin) |
| http://127.0.0.1:8000/api/docs | OpenAPI / Swagger UI (also `/api/redoc`) |

### Seed data

`scripts/seed.py` is idempotent, so it's safe to re-run. It creates:

- 5 categories and 19 dishes (English + Khmer names and descriptions, with photos).
- One sold-out dish (Pumpkin Custard) and one low-stock dish (Mango Sticky Rice).
- Default store settings.
- The first admin account.

`--demo-orders` adds realistic order history so the dashboard and reports have data. `--reset` wipes menu and order data first (development only).

Food photos come from Pexels and Unsplash under their free licenses. Credits are in [backend/seed_media/SOURCES.md](backend/seed_media/SOURCES.md).

### Admin access

No default admin password exists. On first seed:

- If `SEED_ADMIN_PASSWORD` is set (≥ 10 characters), that becomes the password.
- Otherwise a random password is generated and printed **once**.

After logging in, an admin can create more staff or admin accounts under **Settings → Team**.

Roles:

| Role | Can do |
|---|---|
| `admin` | Everything. |
| `staff` | Dashboard, orders, inventory, customers, payments and reports. Can't edit the menu, settings or team. |
| `customer` | Optional account for order history. Guests can order without one. |

Roles are enforced by the API, not just hidden in the UI.

## 4. Demo payment workflow

1. The student places an order. The API recomputes every price from the database, locks the food rows, reserves stock, and opens a **pending** payment that expires after 15 minutes.
2. The payment page shows the amount, a demo QR code, a countdown, and the banner **"DEMO PAYMENT — NO REAL MONEY WILL BE TRANSFERRED"**.
3. **Simulate Payment** calls `POST /api/v1/payments/demo/confirm`. The API checks the caller owns the order and that the payment belongs to it, then marks it **paid** and the order **confirmed**. Repeating the call is harmless (idempotent).
4. The student sees a success screen and a live tracking page. The order appears for staff in `/admin/orders`.
5. Unpaid orders expire automatically, and their reserved stock is released exactly once.

Details, security rules and the plan for a real KHQR provider are in [docs/payment-demo.md](docs/payment-demo.md).

## 5. Tests

```bash
# Backend: 56 tests against a real PostgreSQL test database (migrated with Alembic)
cd backend && uv run pytest
uv run ruff check . && uv run ruff format --check .

# Frontend: unit tests (Node) + component tests (real Chromium via Vitest browser mode)
cd frontend && npm test
npm run check          # svelte-check / TypeScript
npm run lint           # Prettier + ESLint

# End-to-end: student journey, mobile cart, admin order processing.
# Needs the database and the API on :8000 running. Builds and serves the app on :4173.
cd frontend && npm run test:e2e
```

## 6. Run everything in Docker (optional)

```bash
docker compose --profile full up -d --build
docker compose --profile full exec backend python scripts/seed.py --demo-orders
```

Then open http://localhost:3000. The API container applies migrations on start. It isn't published on the host: the web container proxies `/api` and `/media` to it.

## 7. Project layout

```text
campuseats/
├── backend/            FastAPI app (app/), Alembic migrations, seed script, pytest suite
├── frontend/           SvelteKit app: routes/(client) for students, routes/admin for staff
├── docs/               architecture, database, API, demo payment, deployment
├── docker/             Postgres init script (creates the test database)
├── docker-compose.yml  db (always) + backend/frontend (profile "full")
└── .env.example
```

More detail:

- [docs/architecture.md](docs/architecture.md)
- [docs/database.md](docs/database.md)
- [docs/api.md](docs/api.md)
- [docs/payment-demo.md](docs/payment-demo.md)
- [docs/deployment.md](docs/deployment.md)
