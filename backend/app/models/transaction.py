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
    source_page = Column(Integer, nullable=True, default=1)
    source_row = Column(Integer, nullable=True)
    raw_text = Column(String, nullable=True, default="")
    extraction_confidence = Column(Float, default=1.0)
    is_low_confidence = Column(Boolean, default=False)
    user_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

