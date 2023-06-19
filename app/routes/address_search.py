from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File

from app import schemas
from app.config import BACKEND_BASE
from app.db import DB, User
from app.users import current_active_user
import requests
from PIL import Image
from secrets import token_hex

router = APIRouter(prefix="/api", tags=["address_search"])


@router.get("/get_address")
async def get_address(q: str):
    response = requests.get(
        f"https://geocode-maps.yandex.ru/1.x/?format=json&geocode={q}&apikey=2f76b727-c21f-491c-b00e-f438c9609773"
    )
    data = response.json()
    # В Yandex API, адреса находятся в data['response']['GeoObjectCollection']['featureMember']
    addresses = [
        geo_object["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"]
        for geo_object in data["response"]["GeoObjectCollection"]["featureMember"]
    ]
    return {"addresses": addresses}
