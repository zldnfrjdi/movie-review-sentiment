from contextlib import asynccontextmanager

import models
import schemas
from database import engine, get_db
from fastapi import Depends, FastAPI, HTTPException
from sentiment import SentimentAnalyzer
from sqlalchemy import func
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)

ml = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml["analyzer"] = SentimentAnalyzer()
    yield
    ml.clear()


app = FastAPI(
    title="Movie Review API",
    description="영화 정보, 사용자 리뷰, 리뷰 감성 분석 API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"], summary="서버 상태 확인")
def root():
    return {"message": "Movie Review API is running"}


@app.post(
    "/movies",
    response_model=schemas.MovieResponse,
    tags=["Movies"],
    summary="영화 등록",
)
def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    db_movie = models.Movie(**movie.model_dump())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


@app.get(
    "/movies",
    response_model=list[schemas.MovieResponse],
    tags=["Movies"],
    summary="전체 영화 조회",
)
def get_movies(db: Session = Depends(get_db)):
    return db.query(models.Movie).all()


@app.get(
    "/movies/{movie_id}",
    response_model=schemas.MovieResponse,
    tags=["Movies"],
    summary="특정 영화 조회",
)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(models.Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return movie


@app.delete("/movies/{movie_id}", tags=["Movies"], summary="영화 삭제")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(models.Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    db.delete(movie)
    db.commit()
    return {"message": f"{movie_id}번 영화가 삭제되었습니다."}


@app.post(
    "/reviews",
    response_model=schemas.ReviewResponse,
    tags=["Reviews"],
    summary="리뷰 등록 (감성 분석 자동 실행)",
)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    if db.get(models.Movie, review.movie_id) is None:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")

    label, score = ml["analyzer"].predict(review.content)

    db_review = models.Review(
        **review.model_dump(),
        sentiment_label=label,
        sentiment_score=score,
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@app.get(
    "/reviews",
    response_model=list[schemas.ReviewResponse],
    tags=["Reviews"],
    summary="리뷰 조회 (limit 미지정 시 전체)",
)
def get_reviews(limit: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Review).order_by(models.Review.created_at.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


@app.get(
    "/movies/{movie_id}/reviews",
    response_model=list[schemas.ReviewResponse],
    tags=["Reviews"],
    summary="특정 영화 리뷰 조회",
)
def get_movie_reviews(movie_id: int, db: Session = Depends(get_db)):
    if db.get(models.Movie, movie_id) is None:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return (
        db.query(models.Review)
        .filter(models.Review.movie_id == movie_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )


@app.delete("/reviews/{review_id}", tags=["Reviews"], summary="리뷰 삭제")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    review = db.get(models.Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
    db.delete(review)
    db.commit()
    return {"message": f"{review_id}번 리뷰가 삭제되었습니다."}


@app.get(
    "/movies/{movie_id}/rating",
    response_model=schemas.RatingResponse,
    tags=["Rating"],
    summary="영화 평점 조회 (감성 점수 평균)",
)
def get_rating(movie_id: int, db: Session = Depends(get_db)):
    if db.get(models.Movie, movie_id) is None:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")

    avg, count = (
        db.query(func.avg(models.Review.sentiment_score), func.count(models.Review.id))
        .filter(models.Review.movie_id == movie_id)
        .one()
    )
    return {
        "movie_id": movie_id,
        "average_score": round(avg, 4) if avg is not None else None,
        "review_count": count,
    }
