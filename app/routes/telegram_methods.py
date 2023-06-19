from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File

from app import schemas
from app.config import BACKEND_BASE
from app.db import DB, User
from app.users import current_active_user
import requests
from PIL import Image
from secrets import token_hex

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.get("/link")
async def get_telegram_link(user: User = Depends(current_active_user), db: DB = Depends(DB)):
    telegram_link = await db.get_telegram_link(user)
    # create a deeplink for telegram bot with start=telegram_link.link_hex

    return {"link": telegram_link.link_hex}
