import os
import hashlib
from datetime import datetime

from sqlalchemy import (Column, Integer, String, Text, DateTime,
                        ForeignKey, create_engine)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'peliculas')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'secret')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(128))
    created_at = Column(DateTime, default=datetime.now)

    reviews = relationship('UserReview', back_populates='user')

    @classmethod
    def create_password(cls, password: str) -> str:
        h = hashlib.md5()
        h.update(password.encode('utf-8'))
        return h.hexdigest()

    @classmethod
    def authenticate(cls, db: Session, username: str, password: str):
        hashed_password = cls.create_password(password)
        return db.query(cls).filter(
            cls.username == username,
            cls.password == hashed_password
        ).first()


class Movie(Base):
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

    reviews = relationship('UserReview', back_populates='movie')


class UserReview(Base):
    __tablename__ = 'user_reviews'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    reviews = Column(Text)
    score = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship('User', back_populates='reviews')
    movie = relationship('Movie', back_populates='reviews')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
