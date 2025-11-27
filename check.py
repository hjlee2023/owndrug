# check.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

conn = sqlite3.connect('fda_news.db')

print("\n" + "="*70)
print("🔍 FDA Monitor DB 상태 체크")
print("="*70 + "\n")

# 1. 전체 통계
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM news")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM news WHERE analyzed = 1")
analyzed = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM news WHERE analyzed = 0")
pending = cursor.fetchone()[0]

print(f"📊 전체 뉴스: {total}건")
print(f"✅ 분석 완료: {analyzed}건")
print(f"⏳ 분석 대기: {pending}건\n")

# 2. 날짜 범위
cursor.execute("SELECT MIN(pub_date), MAX(pub_date) FROM news")
date_range = cursor.fetchone()
if date_range[0]:
    print(f"📅 날짜 범위: {date_range[0]} ~ {date_range[1]}\n")

# 3. 미분석 뉴스도 표시!
cursor.execute("""
    SELECT pub_date, title
    FROM news 
    WHERE analyzed = 0
    ORDER BY pub_date DESC
    LIMIT 10
""")
pending_news = cursor.fetchall()

if pending_news:
    print("="*70)
    print("⏳ 분석 대기 중인 뉴스 (최근 10개)")
    print("="*70 + "\n")
    for row in pending_news:
        print(f"📅 {row[0]}")
        print(f"📰 {row[1][:70]}...")
        print("-" * 70)
    print(f"\n💡 `python analyzer.py` 실행하세요!\n")

# 4. 분석 완료된 뉴스
cursor.execute("""
    SELECT pub_date, title, ticker, impact_score 
    FROM news 
    WHERE analyzed = 1 
    AND ticker IS NOT NULL
    AND ticker != ''
    ORDER BY pub_date DESC
    LIMIT 10
""")
results = cursor.fetchall()

if results:
    print("="*70)
    print("✅ 분석 완료된 뉴스 (티커 있음, 최recent 10개)")
    print("="*70 + "\n")
    for row in results:
        print(f"📅 {row[0]}")
        print(f"📰 {row[1][:60]}...")
        print(f"🏢 티커: {row[2]}")
        print(f"⭐ 점수: {row[3]}")
        print("-" * 70)

conn.close()

print("\n" + "="*70)
print("✅ 체크 완료!")
print("="*70 + "\n")
