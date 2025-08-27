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

from fastapi import FastAPI, HTTPException, Request
from app.shared.subscription_db import upsert_subscription, get_subscription_by_id
from app.backend.utils import start_bot, restart_bot

app = FastAPI()

@app.post("/yookassa/webhook")
async def yookassa_webhook(request: Request):
    """
    Ожидаем JSON вида:
    {
      "event": "payment.succeeded",
      "object": {
         "id": "...",
         "status": "succeeded",
         "metadata": {
             "bot_id": "abcd1234",
             "months": 3
         }
      }
    }
    """
    payload = await request.json()
    try:
        event = payload.get("event")
        obj = payload.get("object", {})
        meta = obj.get("metadata", {}) or {}

        if event != "payment.succeeded":
            return {"status": "ignored"}

        bot_id = meta.get("bot_id")
        months = int(meta.get("months", 1))

        if not bot_id:
            raise HTTPException(status_code=400, detail="metadata.bot_id is required")

        # Берём существующую подписку чтобы знать token/admins
        sub = await get_subscription_by_id(bot_id)
        if not sub:
            raise HTTPException(status_code=404, detail="subscription not found for bot_id")

        bot_token = sub["bot_token"]
        admin_ids = sub["admin_ids"]

        # Продлеваем (active=1, warn_* сбрасываются)
        await upsert_subscription(
            bot_id=bot_id,
            bot_token=bot_token,
            admin_ids=admin_ids,
            months=months,
            trial=False
        )

        # Включим (или перезапустим) бота на всякий случай
        try:
            start_bot(bot_id)      # если был остановлен
        except Exception:
            pass
        try:
            restart_bot(bot_id)    # если уже работал — применим свежую .env/логику
        except Exception:
            pass

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
