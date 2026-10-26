import re
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

USERNAME_RE = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(min_length=1, max_length=8192)


class AuthUser(BaseModel):
    id: int
    first_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_admin: bool = False


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUser


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    category: str
    name_uz: str
    name_ru: str
    name_en: str
    description: str
    amount: int
    price: Decimal
    currency: str


class AdminProductOut(ProductOut):
    is_active: bool
    fulfilment_mode: str


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)
    # Required: who receives the Stars/Premium. Telegram passwords or codes are never collected.
    customer_details: dict[str, str]
    idempotency_key: str = Field(min_length=12, max_length=128)

    @field_validator("customer_details")
    @classmethod
    def _check_details(cls, v: dict[str, str]) -> dict[str, str]:
        if set(v) - {"telegram_username"}:
            raise ValueError("Only telegram_username is accepted")
        username = v.get("telegram_username", "").strip()
        if not USERNAME_RE.match(username):
            raise ValueError("telegram_username must look like @username (5-32 letters, digits, _)")
        return {"telegram_username": "@" + username.lstrip("@")}


class OrderOut(BaseModel):
    id: str
    product_id: int
    quantity: int
    total_amount: Decimal
    currency: str
    status: str
    message: str = ""
    created_at: datetime | None = None
    status_text: str = ""


class AdminOrderOut(OrderOut):
    product_name: str = ""
    customer_telegram_id: int = 0
    customer_username: str | None = None
    customer_details: dict[str, str] = Field(default_factory=dict)


class TransitionRequest(BaseModel):
    to_status: str = Field(min_length=3, max_length=32)
    note: str = Field(default="", max_length=200)


class ProductIn(BaseModel):
    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9_\-]+$")
    category: Literal["stars", "premium"]
    name_uz: str = Field(min_length=1, max_length=160)
    name_ru: str = Field(min_length=1, max_length=160)
    name_en: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=1000)
    amount: int = Field(ge=1, le=1_000_000)  # Stars quantity or Premium days
    price: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default="UZS", min_length=3, max_length=3)
    is_active: bool = False


class ProductPatch(BaseModel):
    name_uz: str | None = Field(default=None, min_length=1, max_length=160)
    name_ru: str | None = Field(default=None, min_length=1, max_length=160)
    name_en: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    is_active: bool | None = None
