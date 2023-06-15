from fastapi import APIRouter, Depends, HTTPException

from app.db import DB, User
import app.schemas
from app.users import current_active_user

router = APIRouter(prefix="/api", tags=["shop"])


@router.get("/products", response_model=list[app.schemas.ProductShort])
async def get_products(db: DB = Depends(DB)):
    return await db.get_products()


@router.get("/products/search", response_model=list[app.schemas.ProductShort])
async def search_products(query: str, db: DB = Depends(DB)):
    return await db.search_products(query)


@router.get("/products/{product_id}", response_model=app.schemas.Product)
async def get_product(product_id: int, db: DB = Depends(DB)):
    return await db.get_product(product_id)


@router.post("/products", response_model=app.schemas.Product)
async def create_product(product: app.schemas.ProductCreate, db: DB = Depends(DB)):
    return await db.create_product(product)


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: DB = Depends(DB)):
    try:
        await db.delete_product(product_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"id": product_id}


# Basket
@router.get("/basket", response_model=app.schemas.Basket)
async def get_basket(db: DB = Depends(DB), user: User = Depends(current_active_user)):
    return await db.get_basket(user)


# add to basket
@router.post("/basket/{product_id}", response_model=app.schemas.BasketItem)
async def add_to_basket(
        product_id: int, db: DB = Depends(DB), user: User = Depends(current_active_user)
):
    basket = await db.get_basket(user)
    return await db.add_to_basket(basket.id, product_id)


# remove from basket
@router.delete(
    "/basket/{product_id}"
)
async def remove_from_basket(
        product_id: int, db: DB = Depends(DB), user: User = Depends(current_active_user)
):
    basket = await db.get_basket(user)
    quantity = await db.remove_from_basket(basket.id, product_id)
    return {"quantity": quantity}
