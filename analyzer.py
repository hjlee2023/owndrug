# analyzer.py
import requests
import sqlite3
import time
import re
import os

API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

def test_api():
    """API 테스트"""
    print("🔑 Testing API...")
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": "Say OK"}],
        "max_tokens": 10
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            print("✅ API works!\n")
            return True
        else:
            print(f"❌ Error {r.status_code}\n")
            return False
    except Exception as e:
        print(f"❌ {e}\n")
        return False

def analyze_news_smart(title, summary):
    """스마트 분석 - Perplexity가 직접 판단"""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # ★ Perplexity에게 맡기기
    prompt = f"""Analyze this FDA news and identify the pharmaceutical companyand give a one-line summary in Korean. Impact는 해당 회사의 주가에 얼마나 영향을 미칠지를 평가하는 것으로, 주가 움직임의 절댓값이 시가총액의 크기와 반비례함을 이용하면 됩니다. 7점 이상이면 고영향으로, 상당한 주가 상승이 예측되고, 3점 이하이면 상당한 주가 하락이 예측되는 경우입니다.:

Title: {title}
Summary: {summary if summary else 'N/A'}

Please answer in this exact format:
Company: [Company name]
Ticker: [US stock ticker, e.g., ARWR]
Type: [approval/warning/breakthrough/rejection/policy]
Impact: [score 0-10]
KoreanSummary: [한 줄 요약, 20자 이내 한국어]
If no specific company is mentioned, write "Ticker: NONE"."""
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 200
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if r.status_code != 200:
            print(f"API Error {r.status_code}")
            return None
        
        result = r.json()
        content = result['choices'][0]['message']['content']
        
        print(f"AI Response:\n{content}\n")
        
        # 파싱
        ticker_match = re.search(r'Ticker:\s*([A-Z]{2,5}|NONE)', content, re.IGNORECASE)
        type_match = re.search(r'Type:\s*(\w+)', content, re.IGNORECASE)
        impact_match = re.search(r'Impact:\s*([\d.]+)', content)
        summary_ko_match = re.search(r'KoreanSummary:\s*(.+)', content)

        if ticker_match:
            ticker = ticker_match.group(1).upper()
            news_type = type_match.group(1).lower() if type_match else 'unknown'
            impact = float(impact_match.group(1)) if impact_match else 5.0
            summary_ko = summary_ko_match.group(1).strip() if summary_ko_match else ""

            if ticker == 'NONE':
                return None
            
            return {
                'ticker': ticker,
                'score': impact,
                'type': news_type, 
                'summary_ko': summary_ko
            }
        
        return None
        
    except Exception as e:
        print(f"Exception: {e}")
        return None

def analyze_all_pending():
    """메인"""
    print("\n" + "="*60)
    print("🤖 Smart AI Analysis with Perplexity")
    print("="*60 + "\n")
    
    if not test_api():
        return
    
    print("="*60 + "\n")
    
    conn = sqlite3.connect('fda_news.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, summary FROM news WHERE analyzed = 0 LIMIT 100")
    pending = cursor.fetchall()
    
    if not pending:
        print("✅ No pending")
        conn.close()
        return
    
    print(f"📰 Analyzing {len(pending)} news...\n")
    
    success = 0
    
    for news_id, title, summary in pending:
        print(f"{title[:70]}...")
        
        result = analyze_news_smart(title, summary)
        
        if result:
            ticker = result['ticker']
            score = result['score']
            news_type = result['type']
            summary_ko = result['summary_ko']
            
            cursor.execute("""
                UPDATE news
                SET ticker = ?, 
                    impact_score = ?, 
                    news_type = ?,
                    summary_ko = ?,
                    analyzed = 1
                WHERE id = ?
            """, (ticker, score, news_type, summary_ko, news_id))
            
            print(f"  ✅ {ticker} | {score} | {news_type}\n")
            success += 1
        else:
            print(f"  ⚠️ No company (policy news)\n")
            
            # 티커 없는 뉴스도 분석 완료로 표시
            cursor.execute("""
                UPDATE news
                SET analyzed = 1, impact_score = 3.0
                WHERE id = ?
            """, (news_id,))
        
        time.sleep(3)
    
    conn.commit()
    conn.close()
    
    print("="*60)
    print(f"🎉 {success}/{len(pending)} companies identified!")
    print("="*60)

if __name__ == "__main__":
    analyze_all_pending()
