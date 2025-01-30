from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Replace with your MySQL connection details
DATABASE_URL = "mysql+aiomysql://root:asus-1971@localhost/projdata"

engine = create_async_engine(DATABASE_URL, echo=True,pool_size=10,         # Set a pool size suitable for your application
    max_overflow=20,      # Allow the pool to expand when needed
    pool_timeout=30,      # Timeout for obtaining a connection
    pool_recycle=3600 )
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False,
)

Base = declarative_base()

# Async function to get the database session
async def get_db():
    async with async_session() as session:
        try:
            # Yield the session to be used in the route or function
            yield session
        except SQLAlchemyError as e:
            # Catch any SQLAlchemy errors and log or handle them as needed
            print(f"Error with the database: {e}")
            # You can re-raise the exception or handle it in a way that suits your needs
            raise
        finally:
            # Ensuring proper cleanup if needed
            await session.close()
