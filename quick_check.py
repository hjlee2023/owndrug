# quick_check.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

conn = sqlite3.connect('fda_news.db')

# 티커 있는 뉴스
df = pd.read_sql_query("""
    SELECT pub_date, title, ticker, impact_score
    FROM news 
    WHERE analyzed = 1 
    AND ticker IS NOT NULL
    AND ticker NOT IN ('THE', 'NEWS', 'FDA')
    ORDER BY pub_date DESC
""", conn)

conn.close()

print("\n=== 분석 완료된 뉴스 (날짜순) ===\n")
print(df)

# 날짜 변환 & 30일 필터
df['pub_date'] = pd.to_datetime(df['pub_date'], errors='coerce')
thirty_days_ago = datetime.now() - timedelta(days=30)

recent = df[df['pub_date'] >= thirty_days_ago]

print(f"\n=== 최근 30일 ({thirty_days_ago.strftime('%Y-%m-%d')} 이후) ===\n")
print(recent)
print(f"\n총 {len(recent)}건")
