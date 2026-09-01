from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# In Supabase, the transaction pooler uses pgbouncer
# pool_pre_ping ensures the connection is alive
engine = create_engine(
    settings.DATABASE_URL.replace("?pgbouncer=true", ""),
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
