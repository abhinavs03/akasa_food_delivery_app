from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from ..security import get_session, get_current_user
from ..models import CartItem, Item, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("")
async def view_cart(request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    cart_items = session.exec(select(CartItem).where(CartItem.user_id == user.id)).all()
    total_cents = sum(ci.quantity * (ci.item.price_cents if ci.item else 0) for ci in cart_items)
    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items, "total_cents": total_cents})

@router.post("/add")
async def add_to_cart(item_id: int = Form(...), quantity: int = Form(1), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    existing = session.exec(select(CartItem).where(CartItem.user_id == user.id, CartItem.item_id == item_id)).first()
    if existing:
        existing.quantity += max(1, quantity)
    else:
        session.add(CartItem(user_id=user.id, item_id=item_id, quantity=max(1, quantity)))
    session.commit()
    return RedirectResponse(url="/cart", status_code=303)

@router.post("/update")
async def update_cart(cart_item_id: int = Form(...), quantity: int = Form(...), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    cart_item = session.get(CartItem, cart_item_id)
    if not cart_item or cart_item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if quantity <= 0:
        session.delete(cart_item)
    else:
        cart_item.quantity = quantity
    session.commit()
    return RedirectResponse(url="/cart", status_code=303)

@router.post("/remove")
async def remove_cart(cart_item_id: int = Form(...), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    cart_item = session.get(CartItem, cart_item_id)
    if not cart_item or cart_item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    session.delete(cart_item)
    session.commit()
    return RedirectResponse(url="/cart", status_code=303)
