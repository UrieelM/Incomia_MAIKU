from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

class FinancialState(Base):
    __tablename__ = "financial_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    current_artificial_salary = Column(Float, default=0.0)
    available_fund = Column(Float, default=0.0)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Float, nullable=False)
    target_salary_at_time = Column(Float, nullable=True) # The target salary calculated dynamically
    created_at = Column(DateTime, default=datetime.utcnow)
