from datetime import datetime, timedelta
import uuid

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserToken
from schemas.user import UserChangePasswordResponse, UserRequest, UserUpdateRequest
from utils import security


# 根据用户名查早数据库
async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 创建用户
async def create_user(db: AsyncSession, user_data: UserRequest):
    # 先把密码加密处理 -> add
    hashed_password = security.get_hash_password(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)  # 从数据库读回最新的 user
    return user


# 创建token
async def create_token(db: AsyncSession, user_id: int):
    # 创建Token -> 设置过期时间 —> 查询数据库当前用户是否有 Token -> 有：更新；没有：添加
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()
    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
    await db.commit()

    return token


# 用户登录
async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None
    return user


# 根据 token查用户: 验证token是否有效 -> 查用户信息
async def get_user_by_token(db: AsyncSession, token: str):
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()
    if not db_token or db_token.expires_at < datetime.now():
        return None

    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 更新用户信息: update更新 -> 检擦是否命中 -> 获取更新后的用户返回
async def update_user_info(
    db: AsyncSession, username: str, user_data: UserUpdateRequest
):
    query = (
        update(User)
        .where(User.username == username)
        .values(**user_data.model_dump(exclude_unset=True, exclude_none=True))
    )
    result = await db.execute(query)
    await db.commit()
    # 检查更新
    if result.rowcount == 0:
        return HTTPException(status_code=404, detail="用户不存在")
    # 获取更新后的用户信息
    update_user = await get_user_by_username(db, username)
    return update_user


# 更新用户密码 token验证 -> 更新密码 -> 返回结果
async def update_user_password(db: AsyncSession, user: User, password_data: UserChangePasswordResponse):
    if not security.verify_password(password_data.old_password, user.password):
        raise HTTPException(status_code=400, detail="旧密码错误")
    hashed_password = security.get_hash_password(password_data.new_password)
    query = (
        update(User).where(User.username == user.username).values(password=hashed_password)
    )
    result = await db.execute(query)
    await db.commit()
    if result.rowcount == 0:
        return HTTPException(status_code=404, detail="用户不存在")
    return True
