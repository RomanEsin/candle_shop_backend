import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class ProductBase(schemas.BaseModel):
    title: str
    price: float

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
    id: int
    user_id: uuid.UUID
    basket_items: list[BasketItem]

    class Config:
        orm_mode = True
