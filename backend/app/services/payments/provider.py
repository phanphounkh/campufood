"""Payment provider interface.

The order/payment workflow only talks to `PaymentProvider`. The MVP ships with
`DemoKHQRProvider`; a real KHQR integration (e.g. via a bank's merchant API) implements
the same interface:

* `create_checkout`  -> ask the provider for a payable KHQR string / deeplink.
* `verify_webhook`   -> validate the provider's signature, then map the event to a
                        `ProviderConfirmation` (reference, amount, currency).
* `refund`           -> request a refund and return the provider reference.

Confirmation itself (locking, idempotency, order state) lives in `service.py` and is shared
by every provider, so a webhook delivered twice can never confirm an order twice.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.models import Order, Payment


@dataclass(frozen=True)
class CheckoutData:
    qr_payload: str
    is_demo: bool


@dataclass(frozen=True)
class ProviderConfirmation:
    payment_id: str
    transaction_reference: str
    amount: Decimal
    currency: str


class PaymentProvider(Protocol):
    name: str

    def create_checkout(self, order: Order, payment: Payment) -> CheckoutData: ...

    def new_transaction_reference(self, payment: Payment) -> str: ...

    def verify_webhook(self, body: bytes, headers: dict[str, str]) -> ProviderConfirmation:
        """Raise if the signature is invalid. Not used by the demo provider."""
        ...

    def refund(self, payment: Payment) -> str: ...
