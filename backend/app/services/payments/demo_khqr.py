"""Demo KHQR provider. No money moves and the QR code is deliberately NOT payable.

The QR payload is a plain-text, human-readable string. It is *not* EMVCo/KHQR-formatted, so
no banking app will recognise it as a payment request, and it does not name any bank or
merchant account.
"""

import secrets

from app.core.errors import AppError
from app.models import Order, Payment
from app.services.payments.provider import CheckoutData, PaymentProvider, ProviderConfirmation

DEMO_QR_PREFIX = "CAMPUSEATS-DEMO"


class DemoKHQRProvider:
    name = "demo_khqr"

    def create_checkout(self, order: Order, payment: Payment) -> CheckoutData:
        payload = "|".join(
            [
                DEMO_QR_PREFIX,
                "NOT-A-REAL-PAYMENT",
                f"order={order.order_number}",
                f"amount={payment.amount:.2f}",
                f"currency={payment.currency}",
                f"ref={payment.id.hex[:12]}",
            ]
        )
        return CheckoutData(qr_payload=payload, is_demo=True)

    def new_transaction_reference(self, payment: Payment) -> str:
        return f"DEMO-{secrets.token_hex(6).upper()}"

    def verify_webhook(self, body: bytes, headers: dict[str, str]) -> ProviderConfirmation:
        raise AppError(400, "NOT_SUPPORTED", "The demo provider does not accept webhooks")

    def refund(self, payment: Payment) -> str:
        return f"DEMO-REFUND-{secrets.token_hex(4).upper()}"


_providers: dict[str, PaymentProvider] = {DemoKHQRProvider.name: DemoKHQRProvider()}


def get_provider(name: str = DemoKHQRProvider.name) -> PaymentProvider:
    return _providers[name]
