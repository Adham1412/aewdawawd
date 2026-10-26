"""Load catalog entries from a JSON file (prices must be set by the operator).

  python scripts/seed_products.py --file scripts/products.example.json --activate

Products stay inactive unless --activate is given. You can also manage products in the admin panel.
"""
import argparse
import asyncio
import json
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from app.db.session import SessionLocal, init_dev_schema
from app.models.entities import Product
from app.schemas.api import ProductIn


async def run(items: list[ProductIn], activate: bool) -> None:
    await init_dev_schema()
    async with SessionLocal() as db:
        for item in items:
            data = item.model_dump()
            data["is_active"] = activate
            found = (await db.execute(select(Product).where(Product.code == item.code))).scalar_one_or_none()
            if found:
                for key, value in data.items():
                    setattr(found, key, value)
            else:
                db.add(Product(**data, fulfilment_mode="manual"))
        await db.commit()
    print(f"Saved {len(items)} products. Active: {activate}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    with open(args.file, encoding="utf-8") as fh:
        raw = json.load(fh)
    items = []
    for entry in raw:
        try:
            Decimal(str(entry["price"]))
            items.append(ProductIn(**entry))
        except (InvalidOperation, ValueError, KeyError) as exc:
            parser.error(f"Invalid product {entry.get('code')!r}: set a real numeric price ({exc})")
    asyncio.run(run(items, args.activate))


if __name__ == "__main__":
    main()
