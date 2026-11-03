# Deployment considerations

The repository ships a production-style Docker setup (`docker compose --profile full`).
Before a real deployment, work through this list.

## Required configuration

| Setting | Production value |
|---|---|
| `APP_ENV` | `production`. The API then refuses weak `JWT_SECRET` values and `COOKIE_SECURE=false`, and disables demo payments. |
| `JWT_SECRET` | 32+ random characters (`openssl rand -hex 32`), stored in a secret manager |
| `COOKIE_SECURE` | `true`. Serve only over HTTPS. |
| `ALLOWED_ORIGINS` / `ORIGIN` / `PUBLIC_ORIGIN` | Your public origin, e.g. `https://eats.example.edu` |
| `DEMO_PAYMENTS_ENABLED` | `false` once a real provider exists (it is forced off in production anyway) |
| `POSTGRES_PASSWORD` | Strong and unique; prefer a managed PostgreSQL with backups and point-in-time recovery |

## Topology

```text
Internet ─► TLS reverse proxy (Caddy / Nginx / cloud LB)
              └─► SvelteKit (node build, :3000) ─► FastAPI (:8000, private network) ─► PostgreSQL
```

- Keep the API on a private network. It trusts `X-Forwarded-For` from the web tier (`TRUST_PROXY_HEADERS=true`), so it must never be reachable directly.
- Media (`MEDIA_ROOT`) is a persistent volume. For multiple instances, move it to object storage (S3-compatible) and serve it from a CDN.
- Run migrations once per release (`alembic upgrade head`). The API container does this on start, which is fine for a single instance. Use a release job when you scale out.

## Scaling notes

- The rate limiter and the expiry sweep are per process. With several API instances:
  - move rate limiting to Redis or the reverse proxy;
  - keep the sweep on one instance (`RUN_BACKGROUND_JOBS=false` on the others). It is safe either way, because expiry is lock-protected and idempotent.
- Order status updates use polling (5 s for students, 15 s for staff). Server-Sent Events or WebSockets can replace this later without changing the API contract.
- Add structured logging, request IDs, error tracking (e.g. Sentry) and uptime checks on `/api/v1/health`.

## Security checklist

- [ ] HTTPS everywhere, HSTS at the proxy.
- [ ] A Content-Security-Policy suited to your CDN and fonts. Fonts are self-hosted via Fontsource, and no third-party scripts are loaded.
- [ ] Rotate `JWT_SECRET` to invalidate all sessions if it leaks. Session lifetime is `JWT_EXPIRE_MINUTES` (default 12 h).
- [ ] Back up the database daily and test restores.
- [ ] Create named staff accounts. Don't share the seeded admin.
- [ ] Review upload limits (`MAX_UPLOAD_MB`) and disk quotas.
- [ ] Replace the demo payment provider and complete the webhook and reconciliation work in [payment-demo.md](payment-demo.md).
