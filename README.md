# 키워드 뉴스 → Slack 자동 알림 (완전 무료)

내가 지정한 키워드(회사명, 산업군 등)로 뉴스를 검색해서, 매일 정해진 시간에
최신순 상위 10개를 Slack 채널에 제목+링크로 보내주는 봇입니다.

**이 구성은 AI API를 전혀 쓰지 않아서 100% 무료로 운영됩니다.**
- 뉴스 소스: Google News RSS (키 발급 불필요)
- Slack 전송: Incoming Webhook (무료)
- 매일 자동 실행: GitHub Actions 스케줄러 (무료 티어로 충분)

## 1. Slack Incoming Webhook 만들기

이전 챗봇처럼 복잡한 봇 설정이 필요 없습니다. 훨씬 간단해요.

1. https://api.slack.com/apps → **Create New App** → **From scratch** (기존 앱이 있으면 그거 써도 됨)
2. 왼쪽 메뉴 **Incoming Webhooks** → 켜기(Enable)
3. 아래로 스크롤 → **Add New Webhook to Workspace** 클릭
4. 알림을 받을 채널 선택 → 허용
5. `https://hooks.slack.com/services/...` 형태의 URL이 생성됨 → 복사해두기

## 2. GitHub 저장소에 이 코드 올리기

1. GitHub에서 새 저장소 생성 (Public이어도 무방, Private이어도 무료 티어로 충분)
2. 이 폴더 안의 파일들을 그대로 업로드/푸시

```bash
git init
git add .
git commit -m "키워드 뉴스 슬랙봇"
git branch -M main
git remote add origin <내-저장소-URL>
git push -u origin main
```

## 3. 저장소에 비밀값(Secrets) 등록

저장소 페이지에서 **Settings → Secrets and variables → Actions → New repository secret**

| Name | 값 예시 |
|---|---|
| `SLACK_WEBHOOK_URL` | 1번에서 복사한 `https://hooks.slack.com/services/...` |
| `NEWS_KEYWORDS` | `삼성전자,반도체` (쉼표로 여러 키워드 구분 가능) |

## 4. 실행 시간 조정 (선택)

`.github/workflows/daily_news.yml` 안의 이 줄에서 시간을 바꿀 수 있습니다.

```yaml
- cron: "0 23 * * *"   # UTC 기준. 한국시간(KST) = UTC + 9시간
```

예: 매일 아침 8시(KST)에 받고 싶다면 → UTC 23:00 → `"0 23 * * *"` (이미 기본값이 이렇게 되어 있음)
예: 매일 저녁 6시(KST)에 받고 싶다면 → UTC 09:00 → `"0 9 * * *"`

> GitHub Actions 스케줄은 트래픽이 몰리면 몇 분 정도 늦게 실행될 수 있습니다 (정각 보장은 아님).

## 5. 테스트

GitHub 저장소 → **Actions** 탭 → **Daily Keyword News to Slack** 워크플로우 선택 →
**Run workflow** 버튼으로 즉시 한 번 실행해서 Slack에 메시지가 오는지 확인하세요.

이후로는 매일 지정한 시간에 자동으로 실행됩니다. 내 컴퓨터를 켜둘 필요도 없습니다
(GitHub 서버에서 대신 실행해주기 때문).

## 나중에 확장하고 싶다면

- **한 줄 요약 추가**: 지금은 제목+링크만 보내지만, 나중에 마음이 바뀌면 Claude API를
  한 줄 추가해서 각 기사를 한 줄 요약하게 만들 수 있습니다 (이때부터는 소량의 API 비용 발생).
- **키워드별로 채널 분리**: Webhook을 채널별로 여러 개 만들어서 키워드마다 다른 채널로 보낼 수 있습니다.
- **부정 키워드 필터링**: 특정 단어가 포함된 기사는 제외하는 로직을 추가할 수 있습니다.
