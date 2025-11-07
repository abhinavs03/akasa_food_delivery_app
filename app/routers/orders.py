from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from ..security import get_session, get_current_user
from ..models import CartItem, Item, Order, OrderItem, Payment, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("")
async def list_orders(request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    orders = session.exec(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())).all()
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})

@router.post("/checkout")
async def checkout(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    cart_items = session.exec(select(CartItem).where(CartItem.user_id == user.id)).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Validate stock
    unavailable: list[str] = []
    for ci in cart_items:
        item = session.get(Item, ci.item_id)
        if not item or item.stock < ci.quantity:
            unavailable.append(item.name if item else f"Item {ci.item_id}")
    if unavailable:
        # Persist error via querystring or flash; here simple redirect with message not implemented
        raise HTTPException(status_code=409, detail=f"Not Available: {', '.join(unavailable)}")

    # Create order and decrement stock
    order = Order(user_id=user.id, status="PLACED", tracking_id=str(uuid4()))
    session.add(order)
    session.commit()
    session.refresh(order)

    total_cents = 0
    for ci in cart_items:
        item = session.get(Item, ci.item_id)
        if item is None:
            continue
        item.stock -= ci.quantity
        line_total = item.price_cents * ci.quantity
        total_cents += line_total
        session.add(OrderItem(order_id=order.id, item_id=item.id, quantity=ci.quantity, price_cents_each=item.price_cents))
        session.delete(ci)

    order.total_cents = total_cents
    session.add(order)
    session.commit()

    return RedirectResponse(url=f"/orders/{order.id}", status_code=303)

@router.get("/{order_id}")
async def order_detail(order_id: int, request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    order = session.get(Order, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get payment information
    payment = session.exec(select(Payment).where(Payment.order_id == order.id).order_by(Payment.created_at.desc())).first()
    
    return templates.TemplateResponse("order_detail.html", {"request": request, "order": order, "payment": payment})
