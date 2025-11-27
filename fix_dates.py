# fix_dates.py - 기존 데이터 날짜 수정
import sqlite3
from datetime import datetime, timedelta
from dateutil import parser

conn = sqlite3.connect('fda_news.db')
cursor = conn.cursor()

# 모든 뉴스의 pub_date 다시 파싱
cursor.execute("SELECT id, pub_date FROM news")
all_news = cursor.fetchall()

fixed = 0
for news_id, pub_date in all_news:
    try:
        # 원본 날짜가 RSS 형식이면 다시 파싱
        if 'EDT' in pub_date or 'EST' in pub_date or ',' in pub_date:
            dt = parser.parse(pub_date, tzinfos={'EDT': -4*3600, 'EST': -5*3600})
            new_date = dt.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE news SET pub_date = ? WHERE id = ?", (new_date, news_id))
            fixed += 1
            print(f"✅ {news_id}: {pub_date} → {new_date}")
    except:
        continue

conn.commit()
conn.close()
print(f"\n🎉 {fixed}개 날짜 수정 완료!")