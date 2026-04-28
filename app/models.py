from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, DateTime
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime

Base = declarative_base()

class user(Base):
    __tablename__="users"

    id=Column(Integer,primary_key=True)
    email=Column(String,unique=True)
    password=Column(String)

class Task(Base):
    __tablename__="tasks"

    id=Column(Integer,primary_key=True,index=True)
    text=Column(String)
    description = Column(String, nullable=True)
    date = Column(DateTime, nullable=True)  # 👈 YENİ
    priority=Column(Integer,default=3)
    embedding = Column(Vector(768))
    due_date=Column(DateTime,nullable=True)
    #completed=Column(Integer,default=0)  # 0: not completed, 1: completed
    completed = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"))




class TaskPydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    text: str
    completed: bool
    description: Optional[str] = None
    date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None
    #completed: Optional[int] = 0
    embedding: Optional[List[float]] = None

    @field_validator("embedding", mode="before")
    @classmethod
    def ensure_embedding_list(cls, value):
        if value is None:
            return None
        if isinstance(value, Vector):
            if hasattr(value, "dim"):
                return [float(x) for x in value.dim]
            return value
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        if hasattr(value, "tolist"):
            return [float(x) for x in value.tolist()]
        if hasattr(value, "dim"):
            return [float(x) for x in value.dim]
        return value
