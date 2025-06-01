from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dao.account import Account
from dao.base import Base


class ActivationLink(Base):
    __tablename__ = "activation_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[Account] = relationship("Account", back_populates="activation_links")