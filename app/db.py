import asyncio
import uuid
from functools import wraps
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import Integer, Column, Boolean, String, ForeignKey, select, Float, UUID, Uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, selectinload, lazyload, subqueryload

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    basket = relationship("Basket", back_populates="user")


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    price = Column(Float)


class BasketItem(Base):
    __tablename__ = "basket_item"

    id = Column(Integer, primary_key=True, index=True)
    basket_id = Column(Integer, ForeignKey("basket.id"))
    basket = relationship("Basket", back_populates="basket_items")
    product_id = Column(Integer, ForeignKey("product.id"))
    product = relationship("Product")
    quantity = Column(Integer)


class Basket(Base):
    __tablename__ = "basket"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    user = relationship("User", back_populates="basket")
    basket_items = relationship("BasketItem", back_populates="basket")


class Order(Base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    user = relationship("User")
    basket_id = Column(Integer, ForeignKey("basket.id"))
    basket = relationship("Basket")


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


class DB:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def get_products(self):
        query = select(Product)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_product(self, product_id):
        query = select(Product).filter(Product.id == product_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_product(self, product):
        product = Product(**product.dict())
        self.session.add(product)
        await self.session.commit()
        await self.session.flush()
        await self.session.refresh(product)

        return product

    async def get_basket(self, user: User):
        query = select(Basket).filter(Basket.user_id == user.id).options(selectinload("*"))
        result = await self.session.execute(query)
        basket = result.scalar_one_or_none()
        if not basket:
            basket = Basket(user_id=user.id)
            self.session.add(basket)
            await self.session.commit()
            return await self.get_basket(user)
        return basket

    async def add_to_basket(self, basket_id, product_id):
        query = select(BasketItem).filter(
            BasketItem.basket_id == basket_id,
            BasketItem.product_id == product_id
        ).options(selectinload("*"))
        result = await self.session.execute(query)
        basket_item = result.scalar_one_or_none()

        if basket_item:
            basket_item.quantity += 1
            await self.session.commit()
        else:
            basket_item = BasketItem(
                basket_id=basket_id, product_id=product_id, quantity=0
            )
            self.session.add(basket_item)
            await self.session.commit()
            return await self.add_to_basket(basket_id, product_id)

        return basket_item

    async def remove_from_basket(self, basket_id, product_id):
        query = select(BasketItem).filter(
            BasketItem.basket_id == basket_id,
            BasketItem.product_id == product_id
        ).options(selectinload("*"))
        result = await self.session.execute(query)
        basket_item = result.scalar_one_or_none()

        if basket_item:
            basket_item.quantity -= 1
            if basket_item.quantity == 0:
                await self.session.delete(basket_item)
            await self.session.commit()

            return basket_item.quantity

        return 0

    async def search_products(self, search_term):
        query = select(Product).where(Product.title.like(f"%{search_term}%"))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_product(self, product_id):
        query = select(Product).where(Product.id == product_id)
        result = await self.session.execute(query)
        product = result.scalars().first()
        if product:
            await self.session.delete(product)
            await self.session.commit()
