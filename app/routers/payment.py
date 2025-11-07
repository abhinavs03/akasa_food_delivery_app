import random
import string
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from ..security import get_session, get_current_user
from ..models import CartItem, Item, Order, OrderItem, Payment, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/checkout")
async def checkout_page(request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """Show checkout page with order summary before payment"""
    cart_items = session.exec(select(CartItem).where(CartItem.user_id == user.id)).all()
    if not cart_items:
        return RedirectResponse(url="/cart", status_code=303)
    
    # Calculate total
    total_cents = sum(ci.quantity * (ci.item.price_cents if ci.item else 0) for ci in cart_items)
    
    # Validate stock
    unavailable: list[str] = []
    for ci in cart_items:
        item = session.get(Item, ci.item_id)
        if not item or item.stock < ci.quantity:
            unavailable.append(item.name if item else f"Item {ci.item_id}")
    
    return templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "cart_items": cart_items,
            "total_cents": total_cents,
            "unavailable": unavailable,
        },
    )

@router.post("/create-order")
async def create_order(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """Create order and redirect to payment"""
    try:
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
            raise HTTPException(status_code=409, detail=f"Not Available: {', '.join(unavailable)}")

        # Create order (without payment yet)
        order = Order(
            user_id=user.id,
            status="PENDING_PAYMENT",
            tracking_id=str(uuid4()),
            payment_status="PENDING",
        )
        session.add(order)
        session.commit()
        session.refresh(order)

        total_cents = 0
        for ci in cart_items:
            item = session.get(Item, ci.item_id)
            if item is None:
                continue
            line_total = item.price_cents * ci.quantity
            total_cents += line_total
            session.add(OrderItem(order_id=order.id, item_id=item.id, quantity=ci.quantity, price_cents_each=item.price_cents))

        order.total_cents = total_cents
        session.add(order)
        session.commit()

        return RedirectResponse(url=f"/payment/{order.id}", status_code=303)
    except Exception as e:
        session.rollback()
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating order: {error_msg}")

@router.get("/{order_id}")
async def payment_page(order_id: int, request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """Show payment page for an order"""
    order = session.get(Order, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.payment_status == "PAID":
        return RedirectResponse(url=f"/orders/{order.id}", status_code=303)
    
    return templates.TemplateResponse(
        "payment.html",
        {
            "request": request,
            "order": order,
        },
    )

@router.post("/{order_id}/process")
async def process_payment(
    order_id: int,
    request: Request,
    payment_method: str = Form(...),
    card_number: str = Form(""),
    card_name: str = Form(""),
    card_expiry: str = Form(""),
    card_cvv: str = Form(""),
    upi_id: str = Form(""),
    wallet_provider: str = Form(""),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Process payment for an order"""
    order = session.get(Order, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.payment_status == "PAID":
        return RedirectResponse(url=f"/orders/{order.id}", status_code=303)
    
    # Validate payment method
    valid_methods = ["CREDIT_CARD", "DEBIT_CARD", "UPI", "WALLET"]
    if payment_method not in valid_methods:
        return templates.TemplateResponse(
            "payment.html",
            {
                "request": request,
                "order": order,
                "error": "Invalid payment method selected",
            },
            status_code=400,
        )
    
    # Validate payment details based on method
    if payment_method in ["CREDIT_CARD", "DEBIT_CARD"]:
        if not card_number or not card_name or not card_expiry or not card_cvv:
            return templates.TemplateResponse(
                "payment.html",
                {
                    "request": request,
                    "order": order,
                    "error": "Please fill all card details",
                },
                status_code=400,
            )
        # Basic card validation (demo - in real app, use proper validation)
        if len(card_number.replace(" ", "")) < 13:
            return templates.TemplateResponse(
                "payment.html",
                {
                    "request": request,
                    "order": order,
                    "error": "Invalid card number",
                },
                status_code=400,
            )
    elif payment_method == "UPI":
        if not upi_id or "@" not in upi_id:
            return templates.TemplateResponse(
                "payment.html",
                {
                    "request": request,
                    "order": order,
                    "error": "Please enter a valid UPI ID",
                },
                status_code=400,
            )
    elif payment_method == "WALLET":
        if not wallet_provider:
            return templates.TemplateResponse(
                "payment.html",
                {
                    "request": request,
                    "order": order,
                    "error": "Please select a wallet provider",
                },
                status_code=400,
            )
    
    # Simulate payment processing (in real app, integrate with payment gateway)
    # For demo: 90% success rate
    payment_success = random.random() > 0.1
    
    # Create payment record
    transaction_id = "TXN" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    payment = Payment(
        order_id=order.id,
        amount_cents=order.total_cents,
        payment_method=payment_method,
        payment_status="SUCCESS" if payment_success else "FAILED",
        transaction_id=transaction_id,
        completed_at=datetime.utcnow() if payment_success else None,
    )
    session.add(payment)
    
    if payment_success:
        # Update order status
        order.payment_status = "PAID"
        order.status = "PLACED"
        
        # Decrement stock
        for order_item in order.items:
            item = session.get(Item, order_item.item_id)
            if item:
                item.stock -= order_item.quantity
        
        # Clear cart
        cart_items = session.exec(select(CartItem).where(CartItem.user_id == user.id)).all()
        for ci in cart_items:
            session.delete(ci)
        
        session.commit()
        return RedirectResponse(url=f"/payment/{order_id}/success", status_code=303)
    else:
        session.commit()
        return templates.TemplateResponse(
            "payment.html",
            {
                "request": request,
                "order": order,
                "error": "Payment failed. Please try again or use a different payment method.",
            },
            status_code=400,
        )

@router.get("/{order_id}/success")
async def payment_success(order_id: int, request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """Show payment success page"""
    order = session.get(Order, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    
    payment = session.exec(select(Payment).where(Payment.order_id == order.id).order_by(Payment.created_at.desc())).first()
    
    return templates.TemplateResponse(
        "payment_success.html",
        {
            "request": request,
            "order": order,
            "payment": payment,
        },
    )

