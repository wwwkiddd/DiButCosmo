from sqlalchemy import DateTime, func, String, BIGINT
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    username: Mapped[str] = mapped_column(String(150), nullable=True)
    tokens: Mapped[int] = mapped_column(nullable=False)
    gemini_chat_history: Mapped[list] = mapped_column(JSONB, default=list)
    perplexity_chat_history: Mapped[list] = mapped_column(JSONB, default=list)
    deep_research_chat_history: Mapped[list] = mapped_column(JSONB, default=list)
    gpt_chat_history: Mapped[list] = mapped_column(JSONB, default=list)

class PromoCode(Base):
    __tablename__ = 'promo_code'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(150), unique=True)
    value: Mapped[int] = mapped_column(nullable=False)
    used_by: Mapped[list] = mapped_column(JSONB, default=list)
    date_end: Mapped[DateTime] = mapped_column(DateTime,)




