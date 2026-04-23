from fastapi import FastAPI, HTTPException, Depends, Header, Query
from pydantic import BaseModel, validator
from typing import Optional
from uuid import uuid4
from datetime import datetime
from passlib.context import CryptContext
from jose import jwt, JWTError
from techstore_database import SessionLocal, CategoryModel, ProductModel
from auth_database import UserModel, CartItemModel
from orders_database import OrderModel, OrderItemModel

app = FastAPI(title="TechStore Full API")

SECRET_KEY = "supersecretkey123"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int
    category_id: str

    @validator("price")
    def price_positive(cls, v):
        if v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return v

class ProductUpdate(BaseModel):
    price: Optional[float] = None
    stock: Optional[int] = None

class RegisterData(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

class LoginData(BaseModel):
    username: str
    password: str

class CartAdd(BaseModel):
    product_id: str
    quantity: int = 1

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        db = SessionLocal()
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        db.close()
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

@app.post("/categories", status_code=201)
def create_category(data: CategoryCreate):
    db = SessionLocal()
    category = CategoryModel(id=str(uuid4()), name=data.name, description=data.description)
    db.add(category)
    db.commit()
    category_id = category.id
    category_name = category.name
    category_description = category.description
    db.close()
    return {"id": category_id, "name": category_name, "description": category_description}

@app.get("/categories")
def get_categories():
    db = SessionLocal()
    categories = db.query(CategoryModel).all()
    result = [{"id": c.id, "name": c.name, "description": c.description} for c in categories]
    db.close()
    return result

@app.get("/products")
def get_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    page: int = Query(1),
    limit: int = Query(10)
):
    db = SessionLocal()
    query = db.query(ProductModel)
    if category:
        query = query.filter(ProductModel.category_id == category)
    if search:
        query = query.filter(ProductModel.name.ilike(f"%{search}%"))
    if sort == "price_asc":
        query = query.order_by(ProductModel.price.asc())
    elif sort == "price_desc":
        query = query.order_by(ProductModel.price.desc())
    offset = (page - 1) * limit
    products = query.offset(offset).limit(limit).all()
    result = [{"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "category_id": p.category_id} for p in products]
    db.close()
    return result

@app.post("/products", status_code=201)
def create_product(data: ProductCreate):
    db = SessionLocal()
    category = db.query(CategoryModel).filter(CategoryModel.id == data.category_id).first()
    if not category:
        db.close()
        raise HTTPException(status_code=404, detail="Категория не найдена")
    product = ProductModel(id=str(uuid4()), name=data.name, price=data.price, stock=data.stock, category_id=data.category_id)
    db.add(product)
    db.commit()
    result = {"id": product.id, "name": product.name, "price": product.price, "stock": product.stock, "category_id": product.category_id}
    db.close()
    return result

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
    result = {"id": product.id, "name": product.name, "price": product.price, "stock": product.stock}
    db.close()
    return result

@app.delete("/products/{product_id}")
def delete_product(product_id: str, current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    db = SessionLocal()
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Товар не найден")
    db.delete(product)
    db.commit()
    db.close()
    return {"message": "Товар удалён"}

@app.post("/auth/register", status_code=201)
def register(data: RegisterData):
    db = SessionLocal()
    existing = db.query(UserModel).filter(UserModel.username == data.username).first()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    user = UserModel(id=str(uuid4()), username=data.username, password=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.close()
    return {"message": "Пользователь создан", "username": data.username, "role": data.role}

@app.post("/auth/login")
def login(data: LoginData):
    db = SessionLocal()
    user = db.query(UserModel).filter(UserModel.username == data.username).first()
    db.close()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    token = create_token({"id": user.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me")
def get_me(current_user: UserModel = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "role": current_user.role}

@app.post("/cart", status_code=201)
def add_to_cart(data: CartAdd, current_user: UserModel = Depends(get_current_user)):
    db = SessionLocal()
    product = db.query(ProductModel).filter(ProductModel.id == data.product_id).first()
    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Товар не найден")
    cart_item = CartItemModel(id=str(uuid4()), user_id=current_user.id, product_id=data.product_id, quantity=data.quantity)
    db.add(cart_item)
    db.commit()
    db.close()
    return {"message": "Товар добавлен в корзину"}

@app.get("/cart")
def get_cart(current_user: UserModel = Depends(get_current_user)):
    db = SessionLocal()
    items = db.query(CartItemModel).filter(CartItemModel.user_id == current_user.id).all()
    total = 0
    result = []
    for item in items:
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        if product:
            subtotal = product.price * item.quantity
            total += subtotal
            result.append({"cart_item_id": item.id, "product": product.name, "price": product.price, "quantity": item.quantity, "subtotal": subtotal})
    db.close()
    return {"items": result, "total": total}

@app.delete("/cart/{item_id}")
def delete_cart_item(item_id: str, current_user: UserModel = Depends(get_current_user)):
    db = SessionLocal()
    item = db.query(CartItemModel).filter(CartItemModel.id == item_id, CartItemModel.user_id == current_user.id).first()
    if not item:
        db.close()
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    db.delete(item)
    db.commit()
    db.close()
    return {"message": "Позиция удалена"}

@app.post("/orders/checkout", status_code=201)
def checkout(current_user: UserModel = Depends(get_current_user)):
    db = SessionLocal()
    cart_items = db.query(CartItemModel).filter(CartItemModel.user_id == current_user.id).all()
    if not cart_items:
        db.close()
        raise HTTPException(status_code=400, detail="Корзина пуста")
    total = 0
    for item in cart_items:
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        if not product:
            db.close()
            raise HTTPException(status_code=404, detail="Товар не найден")
        if product.stock < item.quantity:
            db.close()
            raise HTTPException(status_code=400, detail=f"Недостаточно товара '{product.name}' на складе")
        total += product.price * item.quantity
    order_id = str(uuid4())
    order = OrderModel(id=order_id, user_id=current_user.id, total_price=total, status="new", created_at=datetime.now().isoformat())
    db.add(order)
    for item in cart_items:
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        order_item = OrderItemModel(id=str(uuid4()), order_id=order_id, product_id=item.product_id, quantity=item.quantity, price_at_purchase=product.price)
        db.add(order_item)
        product.stock -= item.quantity
        db.delete(item)
    db.commit()
    db.close()
    return {"message": "Заказ оформлен", "order_id": order_id, "total": total, "status": "new"}

@app.get("/my-orders")
def my_orders(current_user: UserModel = Depends(get_current_user)):
    db = SessionLocal()
    orders = db.query(OrderModel).filter(OrderModel.user_id == current_user.id).all()
    result = []
    for order in orders:
        items = db.query(OrderItemModel).filter(OrderItemModel.order_id == order.id).all()
        order_items = []
        for item in items:
            product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
            order_items.append({"product": product.name if product else "Удалён", "quantity": item.quantity, "price_at_purchase": item.price_at_purchase})
        result.append({"order_id": order.id, "status": order.status, "total_price": order.total_price, "created_at": order.created_at, "items": order_items})
    db.close()
    return result

@app.patch("/orders/{order_id}/status")
def update_status(order_id: str, status: str, current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    allowed = ["new", "paid", "shipped", "completed", "cancelled"]
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Статус должен быть одним из: {allowed}")
    db = SessionLocal()
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        db.close()
        raise HTTPException(status_code=404, detail="Заказ не найден")
    order.status = status
    db.commit()
    db.close()
    return {"message": f"Статус изменён на '{status}'"}

@app.get("/admin/stats")
def admin_stats(current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    db = SessionLocal()

    # Количество пользователей
    total_users = db.query(UserModel).count()

    # Общая выручка
    orders = db.query(OrderModel).all()
    total_revenue = sum(o.total_price for o in orders)

    # Топ-3 товара
    from sqlalchemy import func
    top_products = (
        db.query(OrderItemModel.product_id, func.sum(OrderItemModel.quantity).label("total_sold"))
        .group_by(OrderItemModel.product_id)
        .order_by(func.sum(OrderItemModel.quantity).desc())
        .limit(3)
        .all()
    )
    top_result = []
    for product_id, total_sold in top_products:
        product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        top_result.append({"product": product.name if product else "Удалён", "total_sold": total_sold})

    db.close()
    return {"total_users": total_users, "total_revenue": total_revenue, "top_products": top_result}

@app.get("/admin/inventory")
def admin_inventory(current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    db = SessionLocal()
    low_stock = db.query(ProductModel).filter(ProductModel.stock < 5).all()
    result = [{"id": p.id, "name": p.name, "stock": p.stock} for p in low_stock]
    db.close()
    return {"low_stock_products": result}