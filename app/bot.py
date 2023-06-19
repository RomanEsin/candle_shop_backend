from telegram import Bot

from app import config
from app.db import Order, Status, DB

bot = Bot(token=config.TELEGRAM_TOKEN)


async def status_updated(db: DB, order: Order, new_status: Status):
    link = await db.get_telegram_link(order.user)
    user_chat_id = link.chat_id
    if not user_chat_id:
        return

    await bot.send_message(
        chat_id=user_chat_id,
        text=f"Ваш заказ обновлен #{order.id}\n{new_status.title}\n{new_status.description}",
    )
