from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from passlib.context import CryptContext
from jose import jwt, JWTError
from auth_database import SessionLocal, UserModel, CartItemModel
from techstore_database import ProductModel

app = FastAPI(title="TechStore Auth API")

# Настройки JWT
SECRET_KEY = "supersecretkey123"
ALGORITHM = "HS256"

# Хеширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схемы данных
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

# Вспомогательные функции
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

# AUTH ЭНДПОИНТЫ
@app.post("/auth/register", status_code=201)
def register(data: RegisterData):
    db = SessionLocal()
    existing = db.query(UserModel).filter(UserModel.username == data.username).first()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    user = UserModel(
        id=str(uuid4()),
        username=data.username,
        password=hash_password(data.password),
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return {"message": "Пользователь создан", "username": user.username, "role": user.role}

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

# КОРЗИНА
@app.post("/cart", status_code=201)
def add_to_cart(data: CartAdd, current_user: UserModel = Depends(get_current_user)):
    db = SessionLocal()
    product = db.query(ProductModel).filter(ProductModel.id == data.product_id).first()
    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Товар не найден")
    cart_item = CartItemModel(
        id=str(uuid4()),
        user_id=current_user.id,
        product_id=data.product_id,
        quantity=data.quantity
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
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
            result.append({
                "cart_item_id": item.id,
                "product": product.name,
                "price": product.price,
                "quantity": item.quantity,
                "subtotal": subtotal
            })
    db.close()
    return {"items": result, "total": total}

@app.delete("/cart/{item_id}")
def delete_cart_item(item_id: str, current_user: UserModel = Depends(get_current_user)):
    db = SessionLocal()
    item = db.query(CartItemModel).filter(
        CartItemModel.id == item_id,
        CartItemModel.user_id == current_user.id
    ).first()
    if not item:
        db.close()
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    db.delete(item)
    db.commit()
    db.close()
    return {"message": "Позиция удалена"}

# ЗАЩИЩЁННЫЕ РОУТЫ (только Admin)
@app.delete("/products/{product_id}")
def admin_delete_product(product_id: str, current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён — нужны права админа")
    db = SessionLocal()
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Товар не найден")
    db.delete(product)
    db.commit()
    db.close()
    return {"message": "Товар удалён"}