# Demo KHQR payment

> **No real money is ever transferred.** The MVP simulates a KHQR checkout so the full order
> lifecycle can be built and tested before a bank integration exists.

## What the student sees

The payment page (`/orders/{id}/pay`) shows:

- The order number and total.
- A countdown until the payment window closes (15 minutes by default, set by the `payment_expiry_minutes` setting).
- The payment status.
- A QR code.
- A permanent banner: **DEMO PAYMENT — NO REAL MONEY WILL BE TRANSFERRED**.

The QR code is deliberately **not payable**. It encodes plain text such as:

```text
CAMPUSEATS-DEMO|NOT-A-REAL-PAYMENT|order=CE-1001|amount=3.75|currency=USD|ref=1ee1266f2c08
```

That text is not EMVCo/KHQR-formatted, so no banking app will treat it as a payment request. It names no bank, merchant account or real KHQR brand asset, and the QR is stamped "DEMO".

## Workflow

1. `POST /orders` locks the food rows, recomputes prices, reserves stock, saves the order (`pending_payment`) and creates a `pending` payment with `expires_at`. All of this happens in one transaction.
2. The page calls `POST /payments/demo/create`. This returns the open payment (idempotent) and the QR payload.
3. **Simulate Payment** calls `POST /payments/demo/confirm` with `{order_id, payment_id}` and the guest's `X-Order-Token` (or the customer session).
4. The API, in one transaction:
   - refuses unless demo mode is on (`DEMO_PAYMENTS_ENABLED=true` and `APP_ENV != production`), returning `403 DEMO_DISABLED`;
   - locks the order, which also proves the caller may access it (otherwise `404`);
   - locks the payment and requires `payment.order_id == order.id` (otherwise `404`);
   - returns the original result with `already_confirmed: true` if the payment is already `paid`;
   - if the payment has expired, cancels the order, releases stock and returns `409 PAYMENT_EXPIRED`;
   - checks the amount against the order total, then sets payment `paid` (with `paid_at` and a `DEMO-…` reference) and order `confirmed`.
5. The success screen links to live tracking (polling every 5 s). The order appears for staff.
6. Unpaid orders expire through a background sweep plus lazy checks; stock is released exactly once.

Payment statuses: `pending`, `paid`, `failed`, `expired`, `cancelled`, `refunded` (`refunded` is used when staff cancel a paid order).

## Security properties

- No endpoint marks an arbitrary order as paid. Confirmation needs order access *and* a matching payment id, and only works in demo mode.
- Concurrent or repeated confirmations are serialised by row locks. A partial unique index allows only one successful payment per order (tested with 5 parallel confirmations).
- Admin payment views and status changes need a staff or admin session.

## Replacing the demo with a real KHQR provider

The workflow only depends on `PaymentProvider` (`backend/app/services/payments/provider.py`):

| Method | Real implementation |
|---|---|
| `create_checkout(order, payment)` | Ask the bank or aggregator for a dynamic KHQR string (amount, currency, bill number = payment id, expiry) |
| `verify_webhook(body, headers)` | Verify the provider's signature (HMAC or public key) and timestamp tolerance, then map the event to a `ProviderConfirmation` |
| `new_transaction_reference` / `refund` | Use the provider's transaction ids and refund API |

Steps:

1. Implement the provider and register it in `services/payments/demo_khqr.py:_providers`, or move the registry to its own module.
2. Add `POST /payments/{provider}/webhook`. It must:
   - verify the signature;
   - deduplicate events by provider event id (store processed ids with a unique constraint);
   - check amount and currency against the payment;
   - call the shared confirmation logic, which is already idempotent and lock-protected.
3. Add reconciliation: a periodic job that queries the provider for `pending` payments near or after expiry and settles mismatches.
4. Set `DEMO_PAYMENTS_ENABLED=false`. The simulate button disappears and `/payments/demo/confirm` returns 403.
5. Never trust the browser for payment success. Confirm only from provider callbacks or reconciliation.
