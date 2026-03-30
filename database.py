from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Подключение к базе данных
# Формат: postgresql://пользователь:пароль@хост/название_бд
DATABASE_URL = "postgresql://postgres:postgres@localhost/todo_db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# Таблица задач
class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    completed = Column(Boolean, default=False)
    createdAt = Column(String)

# Создать таблицу если не существует
Base.metadata.create_all(engine)