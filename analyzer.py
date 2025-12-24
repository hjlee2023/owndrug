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
    prompt = f"""이 제약바이오 뉴스를 분석하고, 기업의 이름과 티커를 식별하고, 한국어로 된 요약을 제공해주세요. Impact는 해당 기업의 주가에 어떤 영향을 얼마나 미칠지 평가하는 지표로, 시가총액이 큰 주식일수록 주가가 잘 움직이지 않는다는 것을 반영하면 됩니다. 5점은 주가가 그대로일 것이라고 예측하는 것이고, 0점은 주가가 가장 크게 하락할 것을, 10점은 주가가 가장 크게 상승할 것을 예측하는 것입니다. 0.1점 단위로 평가해주세요.:

Title: {title}
Summary: {summary if summary else 'N/A'}

Please answer in this exact format:
Company: [Company name]
Ticker: [US stock ticker, e.g., ARWR]
Type: [approval/warning/breakthrough/rejection/policy]
Impact: [score 0-10]
KoreanSummary: [50자 이내, 기업명을 포함한 완성된 문장]
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
