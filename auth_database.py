from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from techstore_database import Base, engine, ProductModel

SessionLocal = sessionmaker(bind=engine)

# Таблица пользователей
class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    cart_items = relationship("CartItemModel", back_populates="user")

# Таблица корзины
class CartItemModel(Base):
    __tablename__ = "cart_items"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    user = relationship("UserModel", back_populates="cart_items")
    product = relationship("ProductModel")

# Создать таблицы
Base.metadata.create_all(engine)