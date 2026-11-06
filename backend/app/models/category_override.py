from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class CategoryOverrideModel(Base):
    __tablename__ = "category_overrides"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_pattern = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

