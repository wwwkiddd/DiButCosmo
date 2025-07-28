import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.backend.models import BotRequest
from app.backend.utils import create_bot_instance

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://telegram-miniapp-builder.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/create_bot/")
async def create_bot(bot_data: BotRequest):
    try:
        bot_info = await create_bot_instance(bot_data)
        return {"status": "ok", "bot_username": bot_info["username"], "bot_id": bot_info["bot_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
