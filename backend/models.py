from datetime import datetime

from database import Base
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    release_date = Column(String)
    director = Column(String)
    genre = Column(String)
    poster_url = Column(String)

    reviews = relationship(
        "Review", back_populates="movie", cascade="all, delete-orphan"
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sentiment_label = Column(String)
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

    movie = relationship("Movie", back_populates="reviews")
