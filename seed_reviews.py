import random

import requests

API_URL = "http://127.0.0.1:8001"
REVIEWS_PER_MOVIE = 12

AUTHORS = [
    "시유",
    "민준",
    "서연",
    "지한",
    "하은",
    "도윤",
    "수아",
    "예준",
    "지민",
    "현우",
    "채원",
    "세하",
    "유나",
    "건우",
    "소율",
]


REVIEWS = [
    "배우들 연기가 정말 좋았어요",
    "영상미가 아름다워서 계속 생각나요",
    "OST가 너무 좋아서 계속 듣고 있어요",
    "두 번 봐도 재밌는 영화",
    "몰입감이 대단했어요 시간 가는 줄 몰랐네요",
    "캐릭터들이 매력적이라 정이 가요",
    "기대 이상이었습니다 강력 추천해요",
    "분위기가 독특해서 좋았어요",
    "감정선이 섬세하게 잘 표현됐어요",
    "엔딩이 여운이 길게 남네요",
    "친구랑 같이 봤는데 둘 다 만족했어요",
    "연출이 세련되고 지루할 틈이 없었어요",
    "주인공 케미가 정말 좋았습니다",
    "인생 영화 하나 추가했습니다",
    "생각보다 훨씬 감동적이었어요",
    "스토리가 지루해서 중간에 졸았어요",
    "기대했는데 너무 실망스러웠다",
    "전개가 너무 느리고 답답했어요",
    "대사가 오글거려서 집중이 안 됐어요",
    "개연성이 부족해서 공감이 안 갔습니다",
    "러닝타임이 너무 길게 느껴졌어요",
    "연기가 어색해서 몰입이 안 됐다",
    "결말이 허무하고 아쉬웠어요",
    "돈이 아까운 영화였습니다",
    "평이 좋아서 봤는데 저랑은 안 맞네요",
    "그냥 무난했어요 나쁘지도 좋지도 않고",
    "원작을 너무 망쳐놓은 것 같아요",
    "CG가 어색해서 깼어요",
    "중반까지는 좋았는데 후반이 별로였다",
    "한 번 볼 만은 한데 다시 보진 않을 듯",
]


def clear_reviews(movie):
    reviews = requests.get(f"{API_URL}/movies/{movie['id']}/reviews", timeout=10).json()
    for r in reviews:
        requests.delete(f"{API_URL}/reviews/{r['id']}", timeout=10).raise_for_status()
    print(f"[{movie['title']}] 기존 리뷰 {len(reviews)}개 삭제")


def build_jobs(movies):
    jobs = []
    for movie in movies:
        contents = random.sample(REVIEWS, REVIEWS_PER_MOVIE)
        authors = random.sample(AUTHORS, REVIEWS_PER_MOVIE)
        for content, author in zip(contents, authors):
            jobs.append((movie, author, content))
    random.shuffle(jobs)
    return jobs


def main():
    movies = requests.get(f"{API_URL}/movies", timeout=10).json()
    print(f"영화 {len(movies)}개 발견\n")

    for movie in movies:
        clear_reviews(movie)
    print()

    for movie, author, content in build_jobs(movies):
        payload = {"movie_id": movie["id"], "author": author, "content": content}
        res = requests.post(f"{API_URL}/reviews", json=payload, timeout=30)
        res.raise_for_status()
        r = res.json()
        print(
            f"[{movie['title']}] {author}: {content} → {r['sentiment_label']} ({r['sentiment_score']})"
        )

    print()
    for movie in movies:
        rating = requests.get(
            f"{API_URL}/movies/{movie['id']}/rating", timeout=10
        ).json()
        print(
            f"== {movie['title']} 평점: {rating['average_score']} / 리뷰 {rating['review_count']}개"
        )


if __name__ == "__main__":
    main()
