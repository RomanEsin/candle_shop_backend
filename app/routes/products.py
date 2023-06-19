from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File

from app import schemas
from app.config import BACKEND_BASE
from app.db import DB, User, ProductType
from app.users import current_active_user
import requests
from PIL import Image
from secrets import token_hex

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/top", response_model=list[schemas.ProductShort])
async def get_top_products(db: DB = Depends(DB)):
    return await db.get_top_products()


@router.get("", response_model=list[schemas.ProductShort])
async def get_products(db: DB = Depends(DB)):
    return await db.get_products()


@router.post("/filter", response_model=list[schemas.ProductShort])
async def get_products(filters: Optional[schemas.ProductFilters], db: DB = Depends(DB)):
    return await db.get_products(filters)


@router.get("/search", response_model=list[schemas.ProductShort])
async def search_products(query: str, db: DB = Depends(DB)):
    return await db.search_products(query)


@router.get("/{product_id}", response_model=schemas.Product)
async def get_product(product_id: int, db: DB = Depends(DB)):
    return await db.get_product(product_id)


@router.post("")
async def create_product(
    title: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    product_type: str = Form(...),
    image: UploadFile = File(...),
    db: DB = Depends(DB),
):
    # check if image is present and is of correct format
    if image:
        if image.content_type.startswith("image/"):
            try:
                # load image
                image_data = Image.open(image.file)

                # Compress image
                image_data = image_data.resize(
                    (image_data.width // 2, image_data.height // 2)
                )

                # create a unique image filename with the original image extension
                image.filename = f"{token_hex(8)}.{image.filename.split('.')[-1]}"

                # Save image
                image_path = f"app/static/{image.filename}"
                image_data.save(image_path)
                image_path = f"{BACKEND_BASE}/api/{image_path}"

            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image file. {e}")

        else:
            raise HTTPException(status_code=400, detail="Invalid file type.")
    else:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    # Create product instance
    product_data = schemas.ProductCreate(
        title=title,
        price=price,
        description=description,
        image=image_path,
        type=ProductType(product_type),
    )

    return await db.create_product(product_data)


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: DB = Depends(DB)):
    try:
        await db.delete_product(product_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"id": product_id}
