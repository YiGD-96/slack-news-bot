"""
키워드 뉴스 상위 10개를 가져와서, 각 기사의 대표 이미지(og:image 메타태그)를
함께 배치한 다이제스트 카드 이미지 한 장을 만듭니다.

AI API를 전혀 사용하지 않습니다:
- 뉴스 목록: Google News RSS (무료)
- 대표 이미지: 각 기사 페이지에 이미 있는 og:image 메타태그 그대로 추출 (무료)
- 이미지 합성: Pillow 라이브러리로 직접 그림 (무료, 로컬 처리)
"""

import os
from io import BytesIO
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

TOP_N = 10
KEYWORDS = [k.strip() for k in os.environ["NEWS_KEYWORDS"].split(",") if k.strip()]
OUTPUT_PATH = "digest/latest.png"

# GitHub Actions ubuntu 러너에 apt로 설치한 나눔고딕 폰트 경로
FONT_BOLD = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

CARD_W = 1000
THUMB_SIZE = 130
ROW_H = 150
PADDING = 40
HEADER_H = 110

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsDigestBot/1.0)"}


def fetch_news_for_keyword(keyword: str) -> list[dict]:
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries:
        try:
            published = parsedate_to_datetime(entry.published)
        except Exception:
            published = datetime.now().astimezone()
        items.append({"title": entry.title, "link": entry.link, "published": published})
    return items


def get_top_items() -> list[dict]:
    all_items = []
    for kw in KEYWORDS:
        all_items.extend(fetch_news_for_keyword(kw))

    seen = set()
    deduped = []
    for it in all_items:
        if it["link"] not in seen:
            seen.add(it["link"])
            deduped.append(it)

    deduped.sort(key=lambda x: x["published"], reverse=True)
    return deduped[:TOP_N]


def extract_og_image(article_url: str) -> str | None:
    """기사 페이지에서 대표 이미지(og:image) URL을 찾습니다. 실패하면 None."""
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=8, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
        if tag and tag.get("content"):
            return tag["content"]
    except Exception:
        pass
    return None


def download_thumbnail(image_url: str, size: int) -> Image.Image | None:
    try:
        resp = requests.get(image_url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        w, h = img.size
        side = min(w, h)
        left, top = (w - side) // 2, (h - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((size, size))
        return img
    except Exception:
        return None


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """한글은 글자 단위로 줄바꿈하는 게 더 안전합니다."""
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        if draw.textlength(test, font=font) > max_width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines[:2]  # 카드가 너무 길어지지 않도록 최대 2줄까지만 표시


def build_digest_image(items: list[dict]) -> None:
    height = HEADER_H + len(items) * ROW_H + PADDING
    canvas = Image.new("RGB", (CARD_W, height), "#FBF6EE")
    draw = ImageDraw.Draw(canvas)

    title_font = ImageFont.truetype(FONT_BOLD, 34)
    item_font = ImageFont.truetype(FONT_BOLD, 22)
    small_font = ImageFont.truetype(FONT_REGULAR, 16)

    today = datetime.now().strftime("%Y-%m-%d")
    draw.text((PADDING, 30), f"[{', '.join(KEYWORDS)}] 오늘의 뉴스 Top {len(items)}", font=title_font, fill="#102A43")
    draw.text((PADDING, 75), today, font=small_font, fill="#8A94A6")

    y = HEADER_H
    for i, item in enumerate(items, 1):
        thumb = None
        og_url = extract_og_image(item["link"])
        if og_url:
            thumb = download_thumbnail(og_url, THUMB_SIZE)

        if thumb:
            canvas.paste(thumb, (PADDING, y + 10))
        else:
            # 이미지를 못 찾은 기사는 빈 회색 박스로 대체
            draw.rectangle([PADDING, y + 10, PADDING + THUMB_SIZE, y + 10 + THUMB_SIZE], fill="#E4DCCC")

        text_x = PADDING + THUMB_SIZE + 24
        text_max_w = CARD_W - text_x - PADDING
        draw.text((text_x, y + 15), f"{i}.", font=item_font, fill="#FF8A4C")

        lines = wrap_text(draw, item["title"], item_font, text_max_w - 46)
        for j, line in enumerate(lines):
            draw.text((text_x + 46, y + 15 + j * 30), line, font=item_font, fill="#102A43")

        y += ROW_H
        draw.line([(PADDING, y - 10), (CARD_W - PADDING, y - 10)], fill="#E4DCCC", width=1)

    out_dir = os.path.dirname(OUTPUT_PATH)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    canvas.save(OUTPUT_PATH)
    print(f"이미지 저장 완료: {OUTPUT_PATH} ({len(items)}건)")


def main():
    items = get_top_items()
    if not items:
        print("가져올 뉴스가 없어 이미지를 만들지 않습니다.")
        return
    build_digest_image(items)


if __name__ == "__main__":
    main()
