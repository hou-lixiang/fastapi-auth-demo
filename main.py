from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError

from database import get_db, engine
from models import Base, User
from auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from pydantic import Field

# 创建数据库表（首次运行自动创建）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="我的API", description="FastAPI + SQLite 学习项目", version="1.0.0")

# ========== 请求/响应模型 ==========

class UserCreate(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

# ========== 公开接口 ==========
@app.post("/register", summary="用户注册")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名或邮箱是否已存在
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名或邮箱已被注册")
    
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "注册成功", "user_id": new_user.id}

@app.post("/login", summary="用户登录")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ========== 认证依赖（用于保护接口） ==========
def get_current_user(token: str = Header(..., alias="Authorization"), db: Session = Depends(get_db)):
    # 客户端发送的 token 格式是 "Bearer xxx"，需要去掉 "Bearer " 前缀
    if token.startswith("Bearer "):
        token = token[7:]
    
    credentials_exception = HTTPException(status_code=401, detail="无效的令牌")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ========== 受保护的接口（需要登录） ==========
@app.get("/me", summary="获取当前用户信息", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, username=current_user.username, email=current_user.email)

@app.get("/users", summary="获取所有用户列表（需要登录）")
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "email": u.email} for u in users]

@app.get("/", summary="根路径")
def root():
    return {"message": "Hello World", "status": "FastAPI + SQLite 已就绪"}