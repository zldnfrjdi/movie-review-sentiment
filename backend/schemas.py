from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MovieCreate(BaseModel):
    title: str = Field(..., description="영화 제목", examples=["트와일라잇"])
    release_date: str | None = Field(
        None, description="개봉일 (YYYY-MM-DD)", examples=["2008-12-10"]
    )
    director: str | None = Field(None, description="감독", examples=["캐서린 하드윅"])
    genre: str | None = Field(None, description="장르", examples=["로맨스, 판타지"])
    poster_url: str | None = Field(None, description="포스터 이미지 URL")


class MovieResponse(MovieCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    movie_id: int = Field(..., description="리뷰할 영화 ID")
    author: str = Field(..., description="작성자 이름", examples=["다혜"])
    content: str = Field(
        ..., description="리뷰 내용", examples=["연출이 정말 좋았어요"]
    )


class ReviewResponse(BaseModel):
    id: int
    movie_id: int
    author: str
    content: str
    sentiment_label: str | None = None
    sentiment_score: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatingResponse(BaseModel):
    movie_id: int
    average_score: float | None = Field(None, description="리뷰 감성 점수 평균")
    review_count: int
