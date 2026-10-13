import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

st.set_page_config(page_title="Movie Review", layout="wide")
st.title("영화 리뷰 서비스")


def api_get(path):
    res = requests.get(f"{API_URL}{path}", timeout=10)
    res.raise_for_status()
    return res.json()


def api_post(path, payload):
    return requests.post(f"{API_URL}{path}", json=payload, timeout=30)


try:
    movies = api_get("/movies")
except requests.RequestException:
    st.error("백엔드 서버에 연결할 수 없습니다.")
    st.stop()

tab_list, tab_add, tab_review, tab_recent = st.tabs(
    ["영화 목록", "영화 추가", "리뷰 작성", "최근 리뷰"]
)

with tab_list:
    if not movies:
        st.info("등록된 영화가 없습니다.")
    else:
        cols = st.columns(4)
        for i, movie in enumerate(movies):
            rating = api_get(f"/movies/{movie['id']}/rating")
            with cols[i % 4]:
                if movie["poster_url"]:
                    st.image(movie["poster_url"], use_container_width=True)
                st.subheader(movie["title"])
                st.caption(
                    f"{movie['director']} · {movie['genre']} · {movie['release_date']}"
                )
                if rating["average_score"] is not None:
                    stars = rating["average_score"] * 5
                    st.markdown(
                        f"평점 **{stars:.1f}** / 5 ({rating['review_count']}개 리뷰)"
                    )
                else:
                    st.markdown("평점 없음")

with tab_add:
    with st.form("add_movie", clear_on_submit=True):
        title = st.text_input("제목")
        release_date = st.date_input("개봉일", value=None)
        director = st.text_input("감독")
        genre = st.text_input("장르")
        poster_url = st.text_input("포스터 URL")
        submitted = st.form_submit_button("등록")

    if submitted:
        if not title:
            st.warning("제목은 필수입니다.")
        else:
            payload = {
                "title": title,
                "release_date": release_date.isoformat() if release_date else None,
                "director": director or None,
                "genre": genre or None,
                "poster_url": poster_url or None,
            }
            res = api_post("/movies", payload)
            if res.status_code == 200:
                st.success(f"'{title}' 등록 완료")
            else:
                st.error(f"등록 실패: {res.text}")

with tab_review:
    if not movies:
        st.info("먼저 영화를 등록하세요.")
    else:
        movie_map = {f"{m['id']}. {m['title']}": m["id"] for m in movies}
        with st.form("add_review", clear_on_submit=True):
            selected = st.selectbox("영화 선택", list(movie_map.keys()))
            author = st.text_input("작성자")
            content = st.text_area("리뷰 내용")
            submitted = st.form_submit_button("리뷰 등록")

        if submitted:
            if not author or not content:
                st.warning("작성자와 리뷰 내용을 입력하세요.")
            else:
                payload = {
                    "movie_id": movie_map[selected],
                    "author": author,
                    "content": content,
                }
                res = api_post("/reviews", payload)
                if res.status_code == 200:
                    r = res.json()
                    st.success("리뷰가 등록되었습니다.")
                    st.metric(
                        label="감성 분석 결과",
                        value=r["sentiment_label"],
                        delta=f"긍정 확률 {r['sentiment_score'] * 100:.1f}%",
                        delta_color="off",
                    )
                else:
                    st.error(f"등록 실패: {res.text}")

with tab_recent:
    title_map = {m["id"]: m["title"] for m in movies}
    options = ["전체 (최근 10개)"] + [f"{m['id']}. {m['title']}" for m in movies]
    choice = st.selectbox("영화 필터", options)

    if choice == options[0]:
        reviews = api_get("/reviews?limit=10")
    else:
        movie_id = int(choice.split(".")[0])
        reviews = api_get(f"/movies/{movie_id}/reviews")

    if not reviews:
        st.info("등록된 리뷰가 없습니다.")
    else:
        df = pd.DataFrame(reviews)
        df["movie_title"] = df["movie_id"].map(title_map)
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        df["sentiment_score"] = (df["sentiment_score"] * 100).round(1).astype(str) + "%"
        df = df[
            [
                "movie_id",
                "movie_title",
                "created_at",
                "author",
                "content",
                "sentiment_label",
                "sentiment_score",
            ]
        ]
        df.columns = [
            "영화 ID",
            "영화 제목",
            "등록일",
            "작성자",
            "리뷰 내용",
            "감성",
            "긍정 확률",
        ]
        st.dataframe(df, use_container_width=True, hide_index=True)
