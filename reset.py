# reset.py
import sqlite3

conn = sqlite3.connect('fda_news.db')
cursor = conn.cursor()

# 모든 뉴스를 미분석 상태로
cursor.execute("UPDATE news SET analyzed = 0")
conn.commit()

# 확인
cursor.execute("SELECT COUNT(*) FROM news WHERE analyzed = 0")
pending = cursor.fetchone()[0]

conn.close()

print(f"✅ Reset complete! {pending} news ready for analysis")
