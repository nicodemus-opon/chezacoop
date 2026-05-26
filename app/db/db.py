import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


load_dotenv()

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url) if db_url else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_engine():
	if engine is None:
		raise RuntimeError('DATABASE_URL is not set.')
	SessionLocal.configure(bind=engine)
	return engine


def get_db() -> Generator[Session, None, None]:
	get_engine()
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
