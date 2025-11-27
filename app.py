# app.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta 


st.set_page_config(page_title="Own Drug 💊", layout="wide", page_icon="💊")


st.title("🔬 Own Drug")
st.caption("바이오테크 투자를 위한 뉴스 AI 분석")
st.markdown("---")


st.info("📢 제약/바이오 기업의 최신 뉴스를 모아보기 쉽게 만들어봤습니다. (AI 분석/티커 식별은 오류가 있을 수 있으며, 투자 결정의 책임은 사용자에게 있습니다.)")
st.info("📢 11월 27일은 미국의 추수감사절입니다. 연휴 전후로는 FDA 승인 소식이 적어집니다.")

# 데이터 로드
@st.cache_data(ttl=10)  # ← 10초로 줄임!
def load_data():
    try:
        conn = sqlite3.connect('fda_news.db')
        
        # 먼저 analyzed=1인 뉴스 확인
        df = pd.read_sql_query("""
            SELECT 
                pub_date as '발표시간',
                COALESCE(summary_ko, title) as '한줄요약',
                ticker as '티커',
                impact_score as '주가영향',
                link as '원문'
            FROM news 
            WHERE analyzed = 1 AND ticker IS NOT NULL
            AND ticker != ''
            AND ticker NOT IN ('THE', 'NEWS', 'FDA', 'FOR', 'AND', 'WITH', 'THIS', 'THAT')
            ORDER BY pub_date DESC 
            LIMIT 30
        """, conn)
        if not df.empty:
            try:
                # 날짜 변환 및 7일 필터링
                df['발표시간'] = pd.to_datetime(df['발표시간'], errors='coerce')

                # 최근 7일만 필터링
                seven_days_ago = datetime.now() - timedelta(days=7)
                df = df[df['발표시간'] >= seven_days_ago]

                # 날짜 포맷
                if not df.empty:
                        df['발표시간'] = df['발표시간'].dt.strftime('%m/%d %H:%M')
            except Exception as e:
                pass

            if not df.empty:
                df['한줄요약'] = df['한줄요약'].str[:60] + '...'

        return df

    except Exception as e:
        st.error(f"DB 오류: {e}")
        return pd.DataFrame()


df = load_data()


# 미분석 뉴스 확인
try:
    conn = sqlite3.connect('fda_news.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM news WHERE analyzed = 0")
    pending = cursor.fetchone()[0]
    conn.close()
except:
    pending = 0


# ★ analyzed_count 먼저 정의
analyzed_count = len(df[df['주가영향'] > 0]) if not df.empty else 0


if df.empty:
    st.warning("📡 최근 7일 이내 분석된 뉴스가 없습니다!")
else:
    # 분석 완료 여부 체크
    if analyzed_count > 0:
        st.success(f"✅ 최근 7일 AI 분석 완료 뉴스 {analyzed_count}건 (티커는 정확하지 않을 수 있습니다.)")
    else:
        st.info(f"📰 뉴스 {len(df)}건 수집됨 (AI 분석 대기)")
    
    if pending > 0:
        st.warning(f"⏳ {pending}개 뉴스 분석 대기 중 → `python analyzer.py` 실행하세요!")
    
    # 점수별 색상
    def color_score(val):
        try:
            if val >= 7:
                return 'background-color: #90EE90; font-weight: bold'
            elif val >= 5:
                return 'background-color: #FFFFE0'
            elif val > 0 and val <= 2:
                return 'background-color: #FFB6C6'
        except:
            pass
        return ''
    
    # 테이블 표시
    st.dataframe(
        df.style.applymap(color_score, subset=['주가영향']),
        use_container_width=True,
        height=500,
        hide_index=True,
        column_config={
            "원문": st.column_config.LinkColumn("원문 링크"),
            "주가영향": st.column_config.NumberColumn("주가영향", format="%.1f ⭐")
        }
    )
    
    # 통계
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 뉴스(7일)", len(df))
    with col2:
        high = len(df[df['주가영향'] >= 7])
        st.metric("고영향 (7+)", high, "🔥" if high > 0 else "")
    with col3:
        if analyzed_count > 0:
            avg = df[df['주가영향'] > 0]['주가영향'].mean()
            st.metric("평균 점수", f"{avg:.1f}")
        else:
            st.metric("평균 점수", "N/A")
    with col4:
        if pending > 0:
            st.metric("분석 대기", pending, "⏳")
        else:
            st.metric("AI 상태", "✅")


st.markdown("---")
st.info("📢 광고를 클릭하시면 저에게 수익이 들어옵니다. 감사합니다.")


st.markdown("---")
st.caption("© Own Drug | 개발: 이현준 | 문의: zpthj1623@naver.com | AI 분석 powered by Perplexity")
st.caption(f"🚀 Phase 2: AI 분석 {'✅ 완료' if analyzed_count > 0 else '⏳ 대기 중'} | 📅 최근 7일")
