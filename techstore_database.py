from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from uuid import uuid4

DATABASE_URL = "postgresql://postgres:postgres@localhost/techstore"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Таблица категорий
class CategoryModel(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    products = relationship("ProductModel", back_populates="category")

# Таблица товаров
class ProductModel(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category_id = Column(String, ForeignKey("categories.id"))
    category = relationship("CategoryModel", back_populates="products")

# Создать таблицы
Base.metadata.create_all(engine)