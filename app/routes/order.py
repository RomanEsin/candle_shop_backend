from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File

from app import schemas
from app.config import BACKEND_BASE
from app.db import DB, User
from app.users import current_active_user
import requests
from PIL import Image
from secrets import token_hex
from app.bot import status_updated

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=schemas.OrderFull)
async def create_order(
        order: schemas.OrderCreate,
        user: User = Depends(current_active_user),
        db: DB = Depends(DB),
):
    order = await db.create_order(order, user)
    await status_updated(db, order, order.status)
    return order


@router.get("", response_model=list[schemas.OrderFull])
async def get_orders(user: User = Depends(current_active_user), db: DB = Depends(DB)):
    return await db.get_orders(user)


@router.put("/{order_id}", response_model=schemas.OrderFull)
async def update_order(order_id: int, order: schemas.OrderUpdate, db: DB = Depends(DB)):
    update = await db.update_order_status(order_id, order.status)
    await status_updated(db, update, order.status)
    return update
