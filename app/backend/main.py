import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from app.backend.models import BotRequest
from app.backend.utils import create_bot_instance
from app.shared.subscription_db import get_expired_bots, init_db

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

