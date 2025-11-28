# collector_gn.py
import feedparser
import sqlite3
from datetime import datetime

from dateutil import parser  # 맨 위 import 쪽에 추가

CLINICAL_KEYWORDS = [
    "phase 1", "phase i",
    "phase 2", "phase ii",
    "phase 3", "phase iii",
    "clinical trial", "clinical study",
    "topline", "top-line",
    "pivotal", "registrational",
    "interim results", "final results",
    "fda", "nda", "bla", "ema",
    "approval", "approves", "authorized", "authorization"
]

# globalnewswire 바이오테크 RSS
RSS_URL = "https://www.globenewswire.com/RssFeed/industry/4577-Pharmaceuticals/feedTitle/GlobeNewswire%20-%20Industry%20News%20on%20Pharmaceuticals"


def collect_news():
    print("\n" + "="*70)
    print("📰 globalnewswire 뉴스 수집 시작")
    print("="*70 + "\n")

    # RSS 파싱
    print(f"🔗 RSS: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("❌ RSS에서 뉴스를 가져오지 못했습니다!")
        print("📦 feedparser 설치 확인: pip install feedparser")
        return

    print(f"✅ RSS에서 {len(feed.entries)}개 항목 발견\n")

    conn = sqlite3.connect('fda_news.db')
    cursor = conn.cursor()

    new_count = 0
    skip_count = 0

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        pub_date = entry.get('published', '')
        summary = entry.get('summary', entry.get('description', ''))[:500]
        guid = entry.get('id', link)

        text = f"{title} {summary}".lower()
        if not any(k in text for k in CLINICAL_KEYWORDS):
            skip_count += 1
            continue

        # 중복 체크 (link 기준) - FDA/다른 소스와도 공통으로 막힘
        cursor.execute("SELECT id FROM news WHERE link = ?", (link,))
        if cursor.fetchone():
            skip_count += 1
            continue

        # 날짜 파싱
        try:
            if pub_date:
                # dateutil로 강력한 파싱
                from dateutil import parser
                try:
                    dt = parser.parse(pub_date)
                    pub_date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    # fallback: 현재 시간
                    pub_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                pub_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pub_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"⚠️ 날짜 파싱 실패: {pub_date}")

        # DB 저장 (source='globe')
        try:
            cursor.execute("""
INSERT INTO news (guid, title, link, pub_date, summary, analyzed, source)
VALUES (?, ?, ?, ?, ?, 0, 'globe')
""", (guid, title, link, pub_date_str, summary))

            print(f"✅ [globe] [{pub_date_str}] {title[:70]}...")
            new_count += 1
        except sqlite3.IntegrityError:
            # UNIQUE 제약 위반 (guid/guid+link 중복)
            skip_count += 1
            continue
        except Exception as e:
            print(f"❌ 저장 실패: {e}")
            continue

    conn.commit()
    conn.close()

    print("\n" + "="*70)
    print(f"🎉 GlobeNewswire(Biotech) 수집 완료: 신규 {new_count}건 | 중복 {skip_count}건")
    print("="*70 + "\n")

    if new_count == 0 and skip_count == 0:
        print("⚠️ 아무것도 수집되지 않았습니다!")
        print("RSS 주소를 확인하거나 인터넷 연결을 확인하세요.")

if __name__ == "__main__":
    collect_news()
