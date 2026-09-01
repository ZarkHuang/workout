import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

db_url = (settings.DATABASE_URL or "sqlite:///./fitpulse.db").strip()

# Strip any accidental 'DATABASE_URL=' or quotes if pasted in Render/env
if db_url.startswith("DATABASE_URL="):
    db_url = db_url.replace("DATABASE_URL=", "", 1).strip()
if (db_url.startswith("'") and db_url.endswith("'")) or (db_url.startswith('"') and db_url.endswith('"')):
    db_url = db_url[1:-1].strip()

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300 if "mysql" in db_url else -1
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
