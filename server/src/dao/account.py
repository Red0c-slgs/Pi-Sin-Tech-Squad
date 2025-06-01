import enum
from datetime import datetime

from sqlalchemy import Column, Boolean, String, Integer, DateTime

from dao.base import Base, next_id_from_sequence_async


class AccountStatus(enum.Enum):
    active = "active"
    deactivated = "deactivated"
    unconfirmed = "unconfirmed"

class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)  # Статус вместо AccountStatus
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    role = Column(String(50), default='user')  # Простая роль вместо сложной системы

    @staticmethod
    async def next_id() -> int:
        return await next_id_from_sequence_async("accounts_id_seq")
