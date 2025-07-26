import uuid
import os
from yookassa import Configuration, Payment
from dotenv import load_dotenv

load_dotenv()

Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")

print("SHOP_ID:", os.getenv("YOOKASSA_SHOP_ID"))
print("SECRET:", os.getenv("YOOKASSA_SECRET_KEY"))

def create_payment_link(amount: int, user_id: int, bot_id: str, months: int) -> str:
    Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
    Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")

    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot"  # или мини-приложение
        },
        "capture": True,
        "description": f"Подписка на {months} мес.",
        "metadata": {
            "user_id": user_id,
            "months": months,
            "bot_id": bot_id
        }
    })
    return payment.confirmation.confirmation_url

from fastapi import APIRouter, Request
from yookassa.domain.notification import WebhookNotificationEventType, WebhookNotificationFactory
from app.shared.subscription_db import prolong_subscription  # нужно реализовать
from datetime import timedelta

router = APIRouter()

@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request):
    body = await request.body()
    notification = WebhookNotificationFactory().create(body, request.headers["Content-Type"])

    if notification.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
        payment = notification.object
        metadata = payment.metadata
        user_id = metadata.get("user_id")
        months = int(metadata.get("months", 1))
        bot_id = metadata.get("bot_id")

        await prolong_subscription(user_id, bot_id, timedelta(days=30 * months))

    return {"status": "ok"}