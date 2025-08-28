import datetime
from sqlalchemy import Column, DateTime, String, Boolean, Integer, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from date_base.database import Base
from typing import Optional, List



# Объявляем классы таблиц

class NewsTable(Base):
    __tablename__ = 'news'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    news_date: Mapped[datetime.datetime]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    source: Mapped[str]
    url: Mapped[str]
    flag: Mapped[str]
    name: Mapped[str]
    # 🔹 Необязательный кластер
    cluster_id: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)

    # 🔹 Необязательный embedding (вектор)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)