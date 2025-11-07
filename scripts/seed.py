import sys
import os
import random
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select

from app.database import engine, create_db_and_tables
from app.models import Category, Item

CATEGORIES = [
    ("All", None),
    ("Fruit", None),
    ("Vegetable", None),
    ("Non-veg", None),
    ("Breads", None),
]

ITEMS = [
    ("Apple", "Fresh red apples", 1200, "Fruit"),
    ("Banana", "Sweet bananas", 400, "Fruit"),
    ("Tomato", "Juicy tomatoes", 500, "Vegetable"),
    ("Chicken Breast", "Boneless chicken", 2200, "Non-veg"),
    ("Whole Wheat Bread", "Healthy bread", 600, "Breads"),
]

def main():
    create_db_and_tables()
    with Session(engine) as session:
        name_to_cat = {}
        for name, _ in CATEGORIES:
            if name == "All":
                continue
            existing = session.exec(select(Category).where(Category.name == name)).first()
            if not existing:
                cat = Category(name=name)
                session.add(cat)
                session.commit()
                session.refresh(cat)
                name_to_cat[name] = cat
            else:
                name_to_cat[name] = existing
        for name, desc, price, cat_name in ITEMS:
            cat = name_to_cat.get(cat_name)
            existing = session.exec(select(Item).where(Item.name == name)).first()
            if not existing and cat:
                session.add(Item(name=name, description=desc, price_cents=price, stock=random.randint(5, 30), category_id=cat.id))
        session.commit()
    print("Seed complete.")

if __name__ == "__main__":
    main()
