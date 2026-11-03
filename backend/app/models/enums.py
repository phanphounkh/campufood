from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


class OrderStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class InventoryReason(StrEnum):
    INITIAL = "initial"
    RESTOCK = "restock"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    ORDER_RESERVED = "order_reserved"
    ORDER_RELEASED = "order_released"
