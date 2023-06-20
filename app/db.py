import asyncio
import enum
import secrets
import uuid
from datetime import datetime
from functools import wraps
from typing import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import (
    Integer,
    Column,
    Boolean,
    String,
    ForeignKey,
    select,
    Float,
    UUID,
    Uuid,
    Enum,
    update,
    DateTime,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    selectinload,
    lazyload,
    subqueryload,
)
from fastapi import status

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    name = Column(String, nullable=False)
    basket = relationship("Basket", back_populates="user")


class ProductType(enum.Enum):
    CANDLE = "candle"
    AROMA_SASHE = "arome_sashe"
    BATH_BOMB = "bath_bomb"


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    price = Column(Float)
    image = Column(String)
    type = Column(Enum(ProductType))


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
    is_ordered = Column(Boolean, default=False)


class Status(enum.Enum):
    CREATED = "created"
    PAID = "paid"
    CANCELED = "canceled"
    DELIVERED = "delivered"

    @property
    def title(self):
        if self == Status.CREATED:
            return "Заказ создан"
        elif self == Status.PAID:
            return "Заказ оплачен"
        elif self == Status.CANCELED:
            return "Заказ отменен"
        elif self == Status.DELIVERED:
            return "Заказ выполнен"

    @property
    def description(self):
        if self == Status.CREATED:
            return "Мы получили ваш заказ и обрабатываем его"
        elif self == Status.PAID:
            return "Мы получили оплату и готовим ваш заказ"
        elif self == Status.CANCELED:
            return "Мы отменили ваш заказ"
        elif self == Status.DELIVERED:
            return "Мы доставили ваш заказ"


class Order(Base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    user = relationship("User")
    basket_id = Column(Integer, ForeignKey("basket.id"))
    basket = relationship("Basket")
    status = Column(Enum(Status), default=Status.CREATED)
    address = Column(String)
    comments = Column(String)
    create_date = Column(DateTime, default=datetime.now())


class TelegramLink(Base):
    __tablename__ = "telegram_link"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    link_hex = Column(String)
    user = relationship("User")
    chat_id = Column(Integer)


class BlogPost(Base):
    __tablename__ = "blog_post"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    image = Column(String)
    create_date = Column(DateTime, default=datetime.now())


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

    async def get_products(self, filters=None):
        price_from = None
        price_to = None
        product_type = None

        if filters:
            price_from = filters.price_from
            price_to = filters.price_to
            product_type = filters.type

        query = select(Product)
        if price_from:
            query = query.filter(Product.price >= price_from)
        if price_to:
            query = query.filter(Product.price <= price_to)
        if product_type:
            query = query.filter(Product.type == product_type)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_product(self, product_id):
        query = select(Product).filter(Product.id == product_id)
        result = await self.session.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        return product

    async def create_product(self, product):
        product = Product(**product.dict())
        self.session.add(product)
        await self.session.commit()
        await self.session.flush()
        await self.session.refresh(product)

        return product

    async def get_basket(self, user: User) -> Basket:
        query = (
            select(Basket)
            .filter(Basket.user_id == user.id, Basket.is_ordered == False)
            .options(selectinload("*"))
        )
        result = await self.session.execute(query)
        basket = result.scalar_one_or_none()
        if not basket:
            basket = Basket(user_id=user.id)
            self.session.add(basket)
            await self.session.commit()
            return await self.get_basket(user)
        return basket

    async def add_to_basket(self, basket_id, product_id):
        # check if product exists
        product = await self.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found",
            )

        query = (
            select(BasketItem)
            .filter(
                BasketItem.basket_id == basket_id, BasketItem.product_id == product_id
            )
            .options(selectinload("*"))
        )
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
        query = (
            select(BasketItem)
            .filter(
                BasketItem.basket_id == basket_id, BasketItem.product_id == product_id
            )
            .options(selectinload("*"))
        )
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

    async def create_order(self, order_create, user: User):
        basket = await self.get_basket(user)
        # if no items in basket
        if not basket.basket_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No items in basket",
            )

        order = Order(
            user_id=user.id,
            basket_id=basket.id,
            address=order_create.address,
            comments=order_create.comments,
        )
        basket.is_ordered = True
        self.session.add(order)
        await self.session.commit()
        await self.session.flush()
        await self.session.refresh(order)

        return await self.get_order_by_id(order.id)

    async def get_order_by_id(self, order_id):
        query = select(Order).filter(Order.id == order_id).options(selectinload("*"))
        result = await self.session.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id {order_id} not found",
            )

        return order

    async def update_order_status(self, order_id, order_status: Status):
        order = await self.get_order_by_id(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id {order_id} not found",
            )

        query = update(Order).where(Order.id == order_id).values(status=order_status)
        await self.session.execute(query)
        await self.session.commit()
        await self.session.flush()

        return await self.get_order_by_id(order_id)

    async def get_all_orders(self):
        query = select(Order).options(selectinload("*"))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_orders(self, user: User):
        query = (
            select(Order).filter(Order.user_id == user.id).options(selectinload("*"))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_top_products(self):
        # get products that have the most orders
        query = (
            select(Product)
            .join(BasketItem)
            .join(Basket)
            .join(Order)
            .group_by(Product.id)
            .order_by(func.count(Order.id).desc())
            .limit(3)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_telegram_link(self, user) -> TelegramLink:
        # check if there is a telegram link else create one and return
        query = select(TelegramLink).filter(TelegramLink.user_id == user.id)
        result = await self.session.execute(query)
        telegram_link = result.scalar_one_or_none()
        if not telegram_link:
            telegram_link = TelegramLink(
                user_id=user.id, link_hex=secrets.token_hex(32)
            )
            self.session.add(telegram_link)
            await self.session.commit()
            await self.session.flush()
            await self.session.refresh(telegram_link)
        return telegram_link

    async def get_telegram_link_by_link_hex(self, link_hex) -> TelegramLink:
        query = select(TelegramLink).filter(TelegramLink.link_hex == link_hex)
        result = await self.session.execute(query)
        link = result.scalar_one_or_none()

        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Telegram link not found",
            )

        return link

    async def get_blog_posts(self):
        query = select(BlogPost).order_by(BlogPost.create_date.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_blog_by_id(self, blog_id):
        query = select(BlogPost).filter(BlogPost.id == blog_id)
        result = await self.session.execute(query)
        blog = result.scalar_one_or_none()

        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found",
            )

        return blog

    async def create_blog_post(self, blog_create):
        blog = BlogPost(
            title=blog_create.title,
            content=blog_create.content,
            image=blog_create.image,
            create_date=datetime.now(),
        )
        self.session.add(blog)
        await self.session.commit()
        await self.session.flush()
        await self.session.refresh(blog)

        return await self.get_blog_by_id(blog.id)

    async def delete_blog(self, blog_id):
        query = select(BlogPost).where(BlogPost.id == blog_id)
        result = await self.session.execute(query)
        blog = result.scalars().first()

        if not blog:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Blog post not found",
            )

        if blog:
            await self.session.delete(blog)
            await self.session.commit()
