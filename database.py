# database.py
import sqlite3


def init_database():
    conn = sqlite3.connect('fda_news.db')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT UNIQUE,
            title TEXT,
            summary TEXT,
            link TEXT,
            pub_date TEXT,
            sentiment_score REAL,
            ticker TEXT,
            confidence REAL,
            news_type TEXT,
            reason TEXT,
            market_cap REAL,
            impact_score REAL,
            analyzed INTEGER DEFAULT 0,
            source TEXT DEFAULT 'fda',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ 데이터베이스 생성 완료!")


if __name__ == "__main__":
    init_database()
