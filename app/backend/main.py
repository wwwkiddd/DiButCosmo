import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from app.backend.models import BotRequest
from app.backend.utils import create_bot_instance
from app.shared.subscription_db import init_db

load_dotenv()

app = FastAPI()

# CORS для Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://telegram-miniapp-builder.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/create_bot/")
async def create_bot(bot_data: BotRequest):
    try:
        username = await create_bot_instance(bot_data)
        return {"status": "ok", "bot_username": username}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Request
from app.shared.subscription_db import prolong_subscription

@app.post("/yookassa/webhook/")
async def yookassa_webhook(request: Request):
    data = await request.json()
    try:
        event = data.get("event")
        if event == "payment.succeeded":
            metadata = data["object"]["metadata"]
            bot_id = metadata.get("bot_id")
            months = int(metadata.get("months", 1))
            await prolong_subscription(bot_id, months)
            return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

