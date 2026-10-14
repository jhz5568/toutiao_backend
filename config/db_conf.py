from sqlalchemy.ext.asyncio import async_session, AsyncSession, create_async_engine

# 数据库 URL
ASYNC_DATABASE_URL = (
    "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8mb4"
)

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # 可选，输出SQL日志
    pool_size=10,  # 设置连接池中保持的持久连接数
    max_overflow=20,  # 设置连接池中的额外连接数
)
