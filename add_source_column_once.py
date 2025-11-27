# add_summary_ko_column_once.py
import sqlite3

conn = sqlite3.connect('fda_news.db')
cursor = conn.cursor()

cursor.execute("ALTER TABLE news ADD COLUMN summary_ko TEXT")
conn.commit()
conn.close()

print("✅ news 테이블에 summary_ko 컬럼 추가 완료")