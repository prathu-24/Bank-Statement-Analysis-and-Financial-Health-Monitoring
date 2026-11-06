from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from app.database import Base

class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    normalized_merchant = Column(String, index=True, default="")
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    balance = Column(Float, nullable=False)
    category = Column(String, index=True, default="Uncategorized")
    user_overridden = Column(Boolean, default=False)
    reference_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

