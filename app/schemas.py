import datetime
import uuid
from typing import Optional

from fastapi_users import schemas

from app.db import Status, ProductType


class UserRead(schemas.BaseUser[uuid.UUID]):
    name: str


class UserCreate(schemas.BaseUserCreate):
    name: str


class UserUpdate(schemas.BaseUserUpdate):
    name: str


class ProductFilters(schemas.BaseModel):
    price_from: Optional[float]
    price_to: Optional[float]
    type: Optional[ProductType]


class ProductBase(schemas.BaseModel):
    title: str
    price: float
    image: str
    type: ProductType

    class Config:
        orm_mode = True


class ProductShort(ProductBase):
    id: int


class ProductCreate(ProductBase):
    description: str


class Product(ProductShort):
    description: str


class BasketItem(schemas.BaseModel):
    id: int
    basket_id: int
    product_id: int
    product: ProductShort
    quantity: int

    class Config:
        orm_mode = True


class Basket(schemas.BaseModel):
    basket_items: list[BasketItem]

    class Config:
        orm_mode = True


class Order(schemas.BaseModel):
    id: int
    status: Status
    basket: Basket
    address: str
    comment: Optional[str]

    class Config:
        orm_mode = True


class OrderCreate(schemas.BaseModel):
    address: str
    comments: Optional[str]


class OrderUpdate(schemas.BaseModel):
    status: Status


class OrderFull(Order):
    create_date: datetime.datetime
