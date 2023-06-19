from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File

from app import schemas
from app.config import BACKEND_BASE
from app.db import DB, User
from app.users import current_active_user
import requests
from PIL import Image
from secrets import token_hex

router = APIRouter(prefix="/api/basket", tags=["basket"])


# Basket
@router.get("", response_model=schemas.Basket)
async def get_basket(db: DB = Depends(DB), user: User = Depends(current_active_user)):
    return await db.get_basket(user)


# add to basket
@router.post("/{product_id}", response_model=schemas.BasketItem)
async def add_to_basket(
    product_id: int, db: DB = Depends(DB), user: User = Depends(current_active_user)
):
    basket = await db.get_basket(user)
    return await db.add_to_basket(basket.id, product_id)


# remove from basket
@router.delete("/{product_id}")
async def remove_from_basket(
    product_id: int, db: DB = Depends(DB), user: User = Depends(current_active_user)
):
    basket = await db.get_basket(user)
    quantity = await db.remove_from_basket(basket.id, product_id)
    return {"quantity": quantity}
