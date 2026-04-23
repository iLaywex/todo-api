from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from techstore_database import Base, engine
from datetime import datetime

# Таблица заказов
class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    total_price = Column(Float, default=0)
    status = Column(String, default="new")
    created_at = Column(String)
    items = relationship("OrderItemModel", back_populates="order")

# Таблица содержимого заказа
class OrderItemModel(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("orders.id"))
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer)
    price_at_purchase = Column(Float)
    order = relationship("OrderModel", back_populates="items")
    product = relationship("ProductModel")

from auth_database import UserModel
Base.metadata.create_all(engine)