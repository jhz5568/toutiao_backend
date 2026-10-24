from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_conf import get_db
from crud import users
from starlette import status

# 整合 根据 Token 查询用户，返回用户
async def get_current_user(authorization:str = Header(default=...,alias="Authorization"),db: AsyncSession = Depends(get_db)):
    #token = authorization.split(" ")[1]  # Bearer token
    token = authorization.replace("Bearer ","")  
    user = await users.get_user_by_token(db,token)
    if not user:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="无效的令牌或令牌已过期")
    return user