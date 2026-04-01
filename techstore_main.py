from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, validator
from typing import Optional
from uuid import uuid4
from techstore_database import SessionLocal, CategoryModel, ProductModel

app = FastAPI(title="TechStore API")

# Схемы данных
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int
    category_id: str

    @validator("price")
    def price_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return v

    @validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Название не может быть пустым")
        return v

class ProductUpdate(BaseModel):
    price: Optional[float] = None
    stock: Optional[int] = None

# КАТЕГОРИИ
@app.post("/categories", status_code=201)
def create_category(data: CategoryCreate):
    db = SessionLocal()
    category = CategoryModel(
        id=str(uuid4()),
        name=data.name,
        description=data.description
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    db.close()
    return category

@app.get("/categories")
def get_categories():
    db = SessionLocal()
    categories = db.query(CategoryModel).all()
    db.close()
    return categories

# ТОВАРЫ
@app.get("/products")
def get_products(category: Optional[str] = Query(None)):
    db = SessionLocal()
    if category:
        products = db.query(ProductModel).filter(ProductModel.category_id == category).all()
    else:
        products = db.query(ProductModel).all()
    db.close()
    return products

@app.post("/products", status_code=201)
def create_product(data: ProductCreate):
    db = SessionLocal()
    category = db.query(CategoryModel).filter(CategoryModel.id == data.category_id).first()
    if not category:
        db.close()
        raise HTTPException(status_code=404, detail="Категория не найдена")
    product = ProductModel(
        id=str(uuid4()),
        name=data.name,
        price=data.price,
        stock=data.stock,
        category_id=data.category_id
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    db.close()
    return product

@app.patch("/products/{product_id}")
def update_product(product_id: str, data: ProductUpdate):
    db = SessionLocal()
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Товар не найден")
    if data.price is not None:
        product.price = data.price
    if data.stock is not None:
        product.stock = data.stock
    db.commit()
    db.refresh(product)
    db.close()
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    db = SessionLocal()
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Товар не найден")
    db.delete(product)
    db.commit()
    db.close()
    return {"message": "Товар удалён"}