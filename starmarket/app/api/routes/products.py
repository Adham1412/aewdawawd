from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import Product
from app.schemas.api import ProductOut

router = APIRouter(tags=["products"])


@router.get("/products", response_model=list[ProductOut], summary="List active products")
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.category, Product.price))
    return list(result.scalars().all())


@router.get("/payment-info", summary="How to pay (set by the operator)")
async def payment_info():
    return {"text": settings.payment_instructions or "To'lov rekvizitlari hali kiritilmagan. Admin bilan bog'laning."}
