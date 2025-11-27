# debug_nvs.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

conn = sqlite3.connect('fda_news.db')

print("\n" + "="*70)
print("🔍 NVS 데이터 디버깅")
print("="*70 + "\n")

# 1. Novartis 관련 모든 뉴스 확인
print("📰 1. Novartis 관련 전체 뉴스 (analyzed 무관)")
df1 = pd.read_sql_query("""
SELECT id, pub_date, title, ticker, analyzed, impact_score
FROM news
WHERE title LIKE '%Novartis%' OR title LIKE '%NVS%' OR title LIKE '%Itvisma%'
ORDER BY id DESC
""", conn)
print(df1)
print(f"\n총 {len(df1)}건\n")

# 2. 11월 24일 모든 뉴스 확인
print("="*70)
print("📅 2. 11월 24일 전체 뉴스")
df2 = pd.read_sql_query("""
SELECT id, pub_date, title, ticker, analyzed
FROM news
WHERE pub_date LIKE '%2025-11-24%'
ORDER BY id DESC
""", conn)
print(df2)
print(f"\n총 {len(df2)}건\n")

# 3. 최근 수집된 뉴스 (날짜 순)
print("="*70)
print("🕐 3. 최근 20개 뉴스 (DB 날짜 순)")
df3 = pd.read_sql_query("""
SELECT id, pub_date, title, ticker, analyzed
FROM news
ORDER BY id DESC
LIMIT 20
""", conn)
print(df3)

# 4. 7일 필터링 테스트
print("\n" + "="*70)
print("⏰ 4. 7일 필터링 테스트")
df4 = pd.read_sql_query("""
SELECT pub_date, title, ticker, analyzed
FROM news
WHERE analyzed = 1 AND ticker IS NOT NULL
ORDER BY id DESC
LIMIT 30
""", conn)
df4['pub_date_converted'] = pd.to_datetime(df4['pub_date'], errors='coerce')
seven_days_ago = datetime.now() - timedelta(days=7)
print(f"오늘: {datetime.now()}")
print(f"7일 전: {seven_days_ago}")
print(f"\n필터링 전: {len(df4)}건")
df4_filtered = df4[df4['pub_date_converted'] >= seven_days_ago]
print(f"필터링 후: {len(df4_filtered)}건\n")
print(df4_filtered[['pub_date', 'title', 'ticker']])

# 5. analyzed=0 확인
print("\n" + "="*70)
print("⏳ 5. 미분석 뉴스")
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM news WHERE analyzed = 0")
pending = cursor.fetchone()[0]
print(f"미분석 뉴스: {pending}건")

if pending > 0:
    df5 = pd.read_sql_query("""
    SELECT id, pub_date, title
    FROM news
    WHERE analyzed = 0
    ORDER BY id DESC
    LIMIT 10
    """, conn)
    print(df5)

conn.close()

print("\n" + "="*70)
print("✅ 디버깅 완료!")
print("="*70 + "\n")
