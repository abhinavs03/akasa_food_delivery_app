from sqlmodel import SQLModel, create_engine
import os

# Import all models so SQLModel can register them
from .models import User, Category, Item, CartItem, Order, OrderItem, Payment  # noqa: F401

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
