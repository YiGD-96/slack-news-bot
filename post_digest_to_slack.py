"""
GitHub 저장소에 커밋된 다이제스트 이미지의 raw 주소를 Slack에 전송합니다.
Slack은 이미지 형식의 URL을 자동으로 미리보기(unfurl)로 펼쳐서 보여주기 때문에,
Incoming Webhook(텍스트 전용)만으로도 사실상 이미지를 전송한 것처럼 보입니다.

주의: 이 방식이 동작하려면 GitHub 저장소가 Public이어야 합니다.
Private 저장소의 raw 주소는 인증 없이는 접근이 안 되어 Slack이 이미지를 못 읽어옵니다.
"""

import os
import time
import requests

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
REPO = os.environ["GITHUB_REPOSITORY"]  # GitHub Actions가 "owner/repo" 형태로 자동 제공
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
IMAGE_PATH = "digest/latest.png"


def main():
    if not os.path.exists(IMAGE_PATH):
        print("이미지 파일이 없어 전송을 건너뜁니다.")
        return

    # 매번 다른 값을 붙여서 Slack이 예전 미리보기를 캐시해서 보여주는 것을 방지
    cache_bust = int(time.time())
    image_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{IMAGE_PATH}?t={cache_bust}"

    resp = requests.post(SLACK_WEBHOOK_URL, json={"text": image_url}, timeout=20)
    resp.raise_for_status()
    print("Slack 전송 완료:", image_url)


if __name__ == "__main__":
    main()
