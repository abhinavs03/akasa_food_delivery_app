from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    cart_items: list["CartItem"] = Relationship(back_populates="user")
    orders: list["Order"] = Relationship(back_populates="user")

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    items: list["Item"] = Relationship(back_populates="category")

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    price_cents: int = 0
    stock: int = 0
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")

    category: Optional[Category] = Relationship(back_populates="items")
    cart_items: list["CartItem"] = Relationship(back_populates="item")
    order_items: list["OrderItem"] = Relationship(back_populates="item")

class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="item.id")
    quantity: int = 1
    added_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="cart_items")
    item: Optional[Item] = Relationship(back_populates="cart_items")

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_cents: int = 0
    status: str = "PLACED"  # PLACED, SHIPPED, DELIVERED, CANCELLED
    tracking_id: str = ""
    payment_status: str = "PENDING"  # PENDING, PAID, FAILED, REFUNDED

    user: Optional[User] = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order")
    payments: list["Payment"] = Relationship(back_populates="order")

class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    amount_cents: int = 0
    payment_method: str = ""  # CREDIT_CARD, DEBIT_CARD, UPI, WALLET
    payment_status: str = "PENDING"  # PENDING, SUCCESS, FAILED
    transaction_id: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    order: Optional[Order] = Relationship(back_populates="payments")

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    item_id: int = Field(foreign_key="item.id")
    quantity: int
    price_cents_each: int

    order: Optional[Order] = Relationship(back_populates="items")
    item: Optional[Item] = Relationship(back_populates="order_items")
