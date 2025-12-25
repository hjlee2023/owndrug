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
st.info("📢 메리 크리스마스~ 12월 25일은 크리스마스입니다. 연휴 전후로는 FDA 승인 소식이 적어집니다.")

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
                # 날짜 변환 및 30일 필터링
                df['발표시간'] = pd.to_datetime(df['발표시간'], errors='coerce')

                # 최근 30일만 필터링
                thirty_days_ago = datetime.now() - timedelta(days=30)
                df = df[df['발표시간'] >= thirty_days_ago]

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
    st.warning("📡 최근 30일 이내 분석된 뉴스가 없습니다!")
else:
    # 분석 완료 여부 체크
    if analyzed_count > 0:
        st.success(f"✅ 최근 30일 AI 분석 완료 뉴스 {analyzed_count}건 (티커는 정확하지 않을 수 있습니다.)")
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
        st.metric("총 뉴스(30일)", len(df))
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
st.info("📢 주가영향 점수가 10점에 가까울수록 큰 주가 상승을, 0점에 가까울수록 큰 주가 하락을 예측합니다.")


st.markdown("---")
st.caption("© Own Drug | 개발: 이현준 | 문의: zpthj1623@naver.com | AI 분석 powered by Perplexity")
st.caption(f"🚀 Phase 2: AI 분석 {'✅ 완료' if analyzed_count > 0 else '⏳ 대기 중'} | 📅 최근 30일")


# app.py 맨 아래에 추가
import random

st.markdown("---")
st.markdown("---")
st.header("🎮 FDA Drug Hunter: 승인 예측 게임")
st.caption("실제 FDA 심사 케이스를 바탕으로 당신의 규제 전문가 실력을 테스트하세요!")

# 실제 FDA 케이스 데이터베이스
DRUG_CASES = [
    {
        "name": "Aduhelm (aducanumab)",
        "company": "Biogen",
        "indication": "알츠하이머병 (경증~중등증)",
        "phase3_result": "2개 임상 중 1개만 성공",
        "primary_endpoint": "CDR-SB (인지기능) 개선 0.39점",
        "biomarker": "Amyloid plaque 59% 감소 ✅",
        "advisory_vote": "0 찬성 / 10 반대 / 1 불확실",
        "safety": "뇌부종(ARIA-E) 35%",
        "answer": True,
        "reason": "바이오마커(아밀로이드 감소)를 surrogate endpoint로 인정하여 신속승인. 역사상 가장 논란이 된 승인으로 3명의 자문위원이 사임함.",
        "ticker": "BIIB",
        "difficulty": "hard"
    },
    {
        "name": "Exondys 51 (eteplirsen)",
        "company": "Sarepta",
        "indication": "듀센 근이영양증 (DMD) - Exon 51 skipping",
        "phase3_result": "pivotal trial 참여자 12명만",
        "primary_endpoint": "6분 보행거리 개선 통계적 유의성 없음",
        "biomarker": "Dystrophin 회복: 12명 중 1명만 >1% 증가",
        "advisory_vote": "자문위원회 권고 거부",
        "safety": "특별한 안전성 문제 없음",
        "answer": True,
        "reason": "대체 치료제가 전무한 희귀질환으로, Janet Woodcock FDA 국장이 직접 개입하여 조건부 승인. 'Need to be capitalized' 발언으로 논란.",
        "ticker": "SRPT",
        "difficulty": "hard"
    },
    {
        "name": "Makena (hydroxyprogesterone)",
        "company": "Covis Pharma",
        "indication": "조산 예방",
        "phase3_result": "확증 임상 실패 (primary endpoint 미달)",
        "primary_endpoint": "조산율 감소 효과 없음",
        "biomarker": "해당 없음",
        "advisory_vote": "철회 권고",
        "safety": "혈전증 위험 신호",
        "answer": False,
        "reason": "2023년 4월 FDA가 승인 철회. 신속승인 후 확증시험 실패 케이스.",
        "ticker": "N/A",
        "difficulty": "easy"
    },
    {
        "name": "Ukoniq (umbralisib)",
        "company": "TG Therapeutics",
        "indication": "재발성 marginal zone lymphoma",
        "phase3_result": "확증시험에서 사망률 증가 시그널",
        "primary_endpoint": "ORR 47% (단일군 시험)",
        "biomarker": "해당 없음",
        "advisory_vote": "신속승인 후 재평가",
        "safety": "치료군 사망률 대조군 대비 높음",
        "answer": False,
        "reason": "2021년 신속승인 후 2022년 6월 자진철수. PI3K inhibitor class effect로 사망률 증가.",
        "ticker": "TGTX",
        "difficulty": "medium"
    },
    {
        "name": "Keytruda (pembrolizumab)",
        "company": "Merck",
        "indication": "PD-L1 양성 비소세포폐암 1차 치료",
        "phase3_result": "KEYNOTE-024 성공",
        "primary_endpoint": "PFS 10.3개월 vs 6.0개월 (HR 0.50, p<0.001)",
        "biomarker": "PD-L1 TPS ≥50%",
        "advisory_vote": "만장일치 찬성",
        "safety": "면역관련 이상반응 관리 가능",
        "answer": True,
        "reason": "명확한 PFS/OS 개선으로 표준치료로 자리잡음. 블록버스터 항암제.",
        "ticker": "MRK",
        "difficulty": "easy"
    },
    {
        "name": "Oxbryta (voxelotor)",
        "company": "Pfizer",
        "indication": "겸상적혈구병 (Sickle Cell Disease)",
        "phase3_result": "확증시험 실패",
        "primary_endpoint": "Hemoglobin 증가 ✅ / 용혈 마커 개선 ✅",
        "biomarker": "VOC(혈관폐색 위기) 감소 효과 없음",
        "advisory_vote": "surrogate endpoint 기반 신속승인",
        "safety": "확증시험에서 사망/뇌졸중 불균형",
        "answer": False,
        "reason": "2024년 시장 철수. Surrogate endpoint(헤모글로빈)는 개선됐으나 임상적 benefit 없음.",
        "ticker": "PFE",
        "difficulty": "medium"
    },
    {
        "name": "Zolgensma (onasemnogene)",
        "company": "Novartis",
        "indication": "척수성 근위축증 (SMA)",
        "phase3_result": "단일군 15명, 대조군 없음",
        "primary_endpoint": "생후 14개월 무보조 앉기 달성",
        "biomarker": "SMN 단백질 발현 증가",
        "advisory_vote": "유전자치료 첫 사례로 특례",
        "safety": "간효소 상승 (관리 가능)",
        "answer": True,
        "reason": "치명적 희귀질환에 유전자치료로 획기적 효과. 사상 최고가 의약품($2.1M).",
        "ticker": "NVS",
        "difficulty": "medium"
    },
    {
        "name": "Leqembi (lecanemab)",
        "company": "Eisai/Biogen",
        "indication": "알츠하이머병 초기",
        "phase3_result": "Clarity AD 성공",
        "primary_endpoint": "CDR-SB 0.45점 개선 (p<0.001)",
        "biomarker": "Amyloid 68% 감소",
        "advisory_vote": "6:0 찬성",
        "safety": "ARIA 12.6% (Aduhelm보다 낮음)",
        "answer": True,
        "reason": "Aduhelm 실패 후 동일 타겟으로 임상적 benefit 입증. 2023년 정식승인.",
        "ticker": "ESALY",
        "difficulty": "medium"
    },
]

# 세션 상태 초기화
if 'game_score' not in st.session_state:
    st.session_state.game_score = 0
if 'game_streak' not in st.session_state:
    st.session_state.game_streak = 0
if 'total_played' not in st.session_state:
    st.session_state.total_played = 0
if 'current_case' not in st.session_state:
    st.session_state.current_case = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'difficulty_filter' not in st.session_state:
    st.session_state.difficulty_filter = "all"

# 난이도 선택
col_diff1, col_diff2, col_diff3, col_diff4 = st.columns(4)
with col_diff1:
    if st.button("🟢 Easy", use_container_width=True):
        st.session_state.difficulty_filter = "easy"
with col_diff2:
    if st.button("🟡 Medium", use_container_width=True):
        st.session_state.difficulty_filter = "medium"
with col_diff3:
    if st.button("🔴 Hard", use_container_width=True):
        st.session_state.difficulty_filter = "hard"
with col_diff4:
    if st.button("🎲 All", use_container_width=True):
        st.session_state.difficulty_filter = "all"

st.caption(f"현재 난이도: **{st.session_state.difficulty_filter.upper()}**")

# 새 케이스 시작
if st.button("🎲 새로운 약물 케이스", use_container_width=True, type="primary"):
    # 난이도 필터링
    if st.session_state.difficulty_filter == "all":
        filtered_cases = DRUG_CASES
    else:
        filtered_cases = [c for c in DRUG_CASES if c['difficulty'] == st.session_state.difficulty_filter]
    
    st.session_state.current_case = random.choice(filtered_cases)
    st.session_state.answered = False
    st.rerun()

# 게임 표시
if st.session_state.current_case:
    case = st.session_state.current_case
    
    # 약물 정보 카드
    st.markdown("### 💊 FDA 심사 대상 약물")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**약물명**: {case['name']}")
        st.markdown(f"**제약사**: {case['company']}")
        st.markdown(f"**적응증**: {case['indication']}")
        st.markdown("---")
        st.markdown("#### 📊 임상시험 데이터")
        st.markdown(f"- **Phase 3 결과**: {case['phase3_result']}")
        st.markdown(f"- **Primary Endpoint**: {case['primary_endpoint']}")
        st.markdown(f"- **Biomarker/Surrogate**: {case['biomarker']}")
        st.markdown(f"- **자문위원회**: {case['advisory_vote']}")
        st.markdown(f"- **안전성**: {case['safety']}")
    
    with col2:
        st.markdown("#### 🤔 당신의 판단은?")
        st.markdown(f"**난이도**: {case['difficulty'].upper()}")
        st.markdown(f"**현재 점수**: {st.session_state.game_score}점")
        st.markdown(f"**연속 정답**: {st.session_state.game_streak}회")
        st.markdown(f"**정답률**: {(st.session_state.game_score / (st.session_state.total_played * 10) * 100) if st.session_state.total_played > 0 else 0:.1f}%")
    
    # 답변 버튼
    if not st.session_state.answered:
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("✅ 승인", use_container_width=True, type="primary"):
                st.session_state.answered = True
                st.session_state.total_played += 1
                
                if case['answer'] == True:
                    bonus = 5 if st.session_state.game_streak >= 3 else 0
                    points = 10 + bonus
                    st.session_state.game_score += points
                    st.session_state.game_streak += 1
                    st.success(f"🎉 정답! +{points}점 {'(연속보너스 +5점!)' if bonus > 0 else ''}")
                else:
                    st.session_state.game_streak = 0
                    st.error("❌ 오답!")
                
                st.rerun()
        
        with col_btn2:
            if st.button("❌ 반려/철회", use_container_width=True, type="secondary"):
                st.session_state.answered = True
                st.session_state.total_played += 1
                
                if case['answer'] == False:
                    bonus = 5 if st.session_state.game_streak >= 3 else 0
                    points = 10 + bonus
                    st.session_state.game_score += points
                    st.session_state.game_streak += 1
                    st.success(f"🎉 정답! +{points}점 {'(연속보너스 +5점!)' if bonus > 0 else ''}")
                else:
                    st.session_state.game_streak = 0
                    st.error("❌ 오답!")
                
                st.rerun()
    
    # 정답 공개
    if st.session_state.answered:
        if case['answer']:
            st.success("### ✅ FDA 결정: 승인")
        else:
            st.error("### ❌ FDA 결정: 반려/철회")
        
        st.info(f"**💡 해설**: {case['reason']}")
        
        if case['ticker'] != "N/A":
            st.markdown(f"**💰 관련 종목**: `{case['ticker']}`")
        
        if st.button("➡️ 다음 케이스", use_container_width=True):
            # 난이도 필터링
            if st.session_state.difficulty_filter == "all":
                filtered_cases = DRUG_CASES
            else:
                filtered_cases = [c for c in DRUG_CASES if c['difficulty'] == st.session_state.difficulty_filter]
            
            st.session_state.current_case = random.choice(filtered_cases)
            st.session_state.answered = False
            st.rerun()

else:
    st.info("👆 위의 '새로운 약물 케이스' 버튼을 눌러 게임을 시작하세요!")
    
    # 게임 설명
    with st.expander("📖 게임 방법"):
        st.markdown("""
        ### 게임 규칙
        1. **실제 FDA 심사 케이스**를 바탕으로 한 임상시험 데이터가 제공됩니다
        2. 제공된 정보를 보고 **승인 또는 반려**를 예측하세요
        3. 정답 시 **10점**, 3연속 정답 시 **보너스 +5점**
        
        ### 난이도
        - 🟢 **Easy**: 명확한 데이터로 판단 쉬움
        - 🟡 **Medium**: 애매한 상황, surrogate endpoint 평가 필요
        - 🔴 **Hard**: 실제로 FDA 내부에서도 논란이 됐던 케이스
        
        ### 팁
        - **Surrogate endpoint**만 개선되고 임상적 benefit이 불명확하면 위험
        - **희귀질환**은 데이터가 부족해도 승인될 수 있음
        - **자문위원회 반대**를 뒤집고 승인된 케이스도 있음 (Aduhelm, Exondys 51)
        - **안전성 시그널**이 있으면 효과가 좋아도 반려될 수 있음
        """)

# 리더보드 (간단 버전)
st.markdown("---")
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
with col_stat1:
    st.metric("🏆 총점", st.session_state.game_score)
with col_stat2:
    st.metric("🔥 연속 정답", st.session_state.game_streak)
with col_stat3:
    st.metric("📊 플레이 횟수", st.session_state.total_played)
with col_stat4:
    if st.session_state.total_played > 0:
        accuracy = (st.session_state.game_score / (st.session_state.total_played * 10) * 100)
        st.metric("🎯 정답률", f"{accuracy:.1f}%")
    else:
        st.metric("🎯 정답률", "0%")

if st.button("🔄 게임 리셋"):
    st.session_state.game_score = 0
    st.session_state.game_streak = 0
    st.session_state.total_played = 0
    st.session_state.current_case = None
    st.session_state.answered = False
    st.rerun()
