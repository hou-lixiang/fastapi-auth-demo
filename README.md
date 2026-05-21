# FastAPI 用户认证系统

这是一个使用 FastAPI + SQLite 构建的用户认证系统。

## 功能

- 用户注册（用户名最少3字符，密码最少6字符）
- 用户登录（返回 JWT token）
- 获取当前用户信息（需要认证）
- 获取所有用户列表（需要认证）

## 技术栈

- FastAPI
- SQLAlchemy (ORM)
- SQLite
- JWT (python-jose)
- bcrypt (密码加密)

## 本地运行

```bash
git clone https://github.com/hou-lixiang/fastapi-auth-demo.git
cd fastapi-auth-demo
pip install -r requirements.txt
uvicorn main:app --reload
