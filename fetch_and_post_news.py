"""
지정한 키워드로 구글 뉴스를 검색해서, 최신순 상위 10개를 Slack으로 전송합니다.

완전 무료로 동작하는 이유:
- 뉴스 소스: Google News RSS (API 키 불필요, 무료)
- Slack 전송: Incoming Webhook (무료)
- 자동 실행: GitHub Actions 스케줄러 (무료 티어)
- Claude/OpenAI 등 AI 호출이 전혀 없음 (제목+링크만 그대로 전달)
"""

import os
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import requests

TOP_N = 10
KEYWORDS = [k.strip() for k in os.environ["NEWS_KEYWORDS"].split(",") if k.strip()]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def fetch_news_for_keyword(keyword: str) -> list[dict]:
    """구글 뉴스 RSS에서 특정 키워드로 검색한 결과를 가져옵니다."""
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)

    items = []
    for entry in feed.entries:
        try:
            published = parsedate_to_datetime(entry.published)
        except Exception:
            published = datetime.now().astimezone()

        source_title = ""
        source = entry.get("source")
        if isinstance(source, dict):
            source_title = source.get("title", "")

        items.append(
            {
                "title": entry.title,
                "link": entry.link,
                "source": source_title,
                "published": published,
            }
        )
    return items


def build_slack_message(items: list[dict], keywords: list[str]) -> str:
    if not items:
        return f"오늘은 '{', '.join(keywords)}' 관련 새 뉴스를 찾지 못했습니다."

    today = datetime.now().strftime("%Y-%m-%d")
    header = f"*[{', '.join(keywords)}] 오늘의 뉴스 Top {len(items)}* ({today})"
    lines = [header, ""]
    for i, item in enumerate(items, 1):
        source_tag = f" _({item['source']})_" if item["source"] else ""
        lines.append(f"{i}. <{item['link']}|{item['title']}>{source_tag}")
    return "\n".join(lines)


def main():
    all_items = []
    for kw in KEYWORDS:
        all_items.extend(fetch_news_for_keyword(kw))

    # 링크 기준 중복 제거 (여러 키워드에 같은 기사가 걸릴 수 있음)
    seen = set()
    deduped = []
    for item in all_items:
        if item["link"] not in seen:
            seen.add(item["link"])
            deduped.append(item)

    # 최신순 정렬 후 상위 N개만 선택
    deduped.sort(key=lambda x: x["published"], reverse=True)
    top_items = deduped[:TOP_N]

    message = build_slack_message(top_items, KEYWORDS)

    response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
    response.raise_for_status()
    print(f"전송 완료: {len(top_items)}건")


if __name__ == "__main__":
    main()
