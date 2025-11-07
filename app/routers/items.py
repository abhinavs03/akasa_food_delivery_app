from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from ..security import get_session
from ..models import Category, Item

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("")
async def list_items(request: Request, category: str | None = Query(default=None), session: Session = Depends(get_session)):
    categories = session.exec(select(Category).order_by(Category.name)).all()
    items_query = select(Item).order_by(Item.name)
    selected_category = None
    if category:
        selected_category = session.exec(select(Category).where(Category.name == category)).first()
        if selected_category:
            items_query = items_query.where(Item.category_id == selected_category.id)
    items = session.exec(items_query).all()
    return templates.TemplateResponse(
        "items.html",
        {
            "request": request,
            "categories": categories,
            "items": items,
            "selected": category or "All",
        },
    )
