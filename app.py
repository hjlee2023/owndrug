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

# 실제 FDA 케이스 데이터베이스 (20개로 확장)
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
        "ticker": "BIIB"
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
        "ticker": "SRPT"
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
        "ticker": "N/A"
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
        "ticker": "TGTX"
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
        "ticker": "MRK"
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
        "ticker": "PFE"
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
        "ticker": "NVS"
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
        "ticker": "ESALY"
    },
    {
        "name": "Opdivo (nivolumab)",
        "company": "Bristol Myers Squibb",
        "indication": "간세포암 (HCC) 1차 치료",
        "phase3_result": "CheckMate-459 실패",
        "primary_endpoint": "OS 16.4개월 vs 14.7개월 (HR 0.85, p=0.075)",
        "biomarker": "PD-L1 상관관계 불명확",
        "advisory_vote": "통계적 유의성 미달",
        "safety": "면역 이상반응 예측 가능",
        "answer": False,
        "reason": "p=0.075로 사전 설정된 0.05 기준 미달. 타 적응증 성공에도 간암은 승인 실패.",
        "ticker": "BMY"
    },
    {
        "name": "Spinraza (nusinersen)",
        "company": "Biogen",
        "indication": "척수성 근위축증 (SMA) 영아형",
        "phase3_result": "ENDEAR 성공 (조기 종료)",
        "primary_endpoint": "운동기능 milestone 달성 41% vs 0%",
        "biomarker": "SMN 단백질 증가",
        "advisory_vote": "만장일치 찬성",
        "safety": "척수강내 주사 합병증",
        "answer": True,
        "reason": "치명적 희귀질환에 첫 치료제. Antisense oligonucleotide 기술의 성공 사례.",
        "ticker": "BIIB"
    },
    {
        "name": "Vascepa (icosapent ethyl)",
        "company": "Amarin",
        "indication": "심혈관 이벤트 감소 (고위험군)",
        "phase3_result": "REDUCE-IT 성공",
        "primary_endpoint": "MACE 25% 감소 (HR 0.75, p<0.001)",
        "biomarker": "중성지방 18% 감소",
        "advisory_vote": "심혈관 benefit 명확",
        "safety": "심방세동 약간 증가",
        "answer": True,
        "reason": "EPA 단독제제로 명확한 심혈관 이득 입증. 2019년 정식 승인.",
        "ticker": "AMRN"
    },
    {
        "name": "Camzyos (mavacamten)",
        "company": "Bristol Myers Squibb",
        "indication": "폐쇄성 비대심근증 (HCM)",
        "phase3_result": "EXPLORER-HCM 성공",
        "primary_endpoint": "pVO2 1.4 mL/kg/min 증가 + NYHA class 개선",
        "biomarker": "LVOT gradient 47 mmHg 감소",
        "advisory_vote": "돌파구 치료제로 인정",
        "safety": "수축기능 저하 모니터링 필요",
        "answer": True,
        "reason": "30년 만의 첫 HCM 치료제. Myosin inhibitor로 새로운 기전.",
        "ticker": "BMY"
    },
    {
        "name": "Lumryz (sodium oxybate)",
        "company": "Avadel",
        "indication": "기면증 (narcolepsy)",
        "phase3_result": "REST-ON 성공",
        "primary_endpoint": "Cataplexy 발작 주당 8.5회 감소",
        "biomarker": "ESS 점수 개선",
        "advisory_vote": "기존 Xyrem의 extended-release 버전",
        "safety": "기존 제제와 유사",
        "answer": True,
        "reason": "1일 1회 투여로 편의성 개선. 2023년 승인.",
        "ticker": "AVDL"
    },
    {
        "name": "Galafold (migalastat)",
        "company": "Amicus",
        "indication": "Fabry disease (amenable mutations)",
        "phase3_result": "FACETS 성공 (소규모)",
        "primary_endpoint": "GI symptoms 개선 + 신장기능 유지",
        "biomarker": "α-Gal A 효소활성 증가",
        "advisory_vote": "경구용 첫 치료제",
        "safety": "두통, 비인두염",
        "answer": True,
        "reason": "효소대체요법 대비 경구 투여 장점. Chaperone 치료제 첫 승인.",
        "ticker": "FOLD"
    },
    {
        "name": "Vyondys 53 (golodirsen)",
        "company": "Sarepta",
        "indication": "듀센 근이영양증 (DMD) - Exon 53 skipping",
        "phase3_result": "단일군 25명",
        "primary_endpoint": "Dystrophin 1.02% 증가",
        "biomarker": "통계적 유의성 없음",
        "advisory_vote": "Exondys 51 선례 따름",
        "safety": "신독성 모니터링",
        "answer": True,
        "reason": "Exondys 51과 동일 논리로 신속승인. Dystrophin 1% 기준 논란 지속.",
        "ticker": "SRPT"
    },
    {
        "name": "Zilretta (triamcinolone)",
        "company": "Flexion",
        "indication": "골관절염 통증 (무릎)",
        "phase3_result": "2개 임상 성공",
        "primary_endpoint": "12주차 통증점수 개선",
        "biomarker": "extended-release 제형",
        "advisory_vote": "기존 약물 제형 변경",
        "safety": "스테로이드 부작용",
        "answer": True,
        "reason": "스테로이드 서방형으로 12주 지속효과. 2017년 승인.",
        "ticker": "FLXN"
    },
    {
        "name": "Omidria (phenylephrine/ketorolac)",
        "company": "Omeros",
        "indication": "백내장 수술 중 동공축소 예방",
        "phase3_result": "수술 중 투여 임상 성공",
        "primary_endpoint": "동공 크기 유지 + 통증 감소",
        "biomarker": "해당 없음",
        "advisory_vote": "수술실 사용 제한적",
        "safety": "기존 약물 조합",
        "answer": True,
        "reason": "수술 중 관류액에 혼합 사용. Niche market. 2014년 승인.",
        "ticker": "OMER"
    },
    {
        "name": "Kynamro (mipomersen)",
        "company": "Kastle (구 Genzyme)",
        "indication": "가족성 고콜레스테롤혈증 (HoFH)",
        "phase3_result": "LDL 25% 감소",
        "primary_endpoint": "통계적으로 유의미",
        "biomarker": "ApoB 감소",
        "advisory_vote": "간독성 우려",
        "safety": "ALT 상승 12%, 지방간",
        "answer": True,
        "reason": "희귀질환 특례로 REMS 프로그램 조건부 승인. 2013년 승인 후 사용 극히 제한적.",
        "ticker": "N/A"
    },
    {
        "name": "Arcalyst (rilonacept)",
        "company": "Regeneron",
        "indication": "통풍 발작 예방",
        "phase3_result": "2개 임상 성공",
        "primary_endpoint": "통풍 발작 빈도 감소",
        "biomarker": "IL-1 차단",
        "advisory_vote": "기존 약물 대비 우월성 불명확",
        "safety": "감염 위험 증가",
        "answer": False,
        "reason": "2012년 통풍 적응증 신청 반려됨. 희귀질환(CAPS)에만 승인 유지. Cost-benefit 문제.",
        "ticker": "REGN"
    },
    {
        "name": "Nuplazid (pimavanserin)",
        "company": "Acadia",
        "indication": "파킨슨병 환각/망상",
        "phase3_result": "-020 성공 / -019 실패",
        "primary_endpoint": "SAPS-PD 5.79점 개선 (vs 2.73점)",
        "biomarker": "5-HT2A 역작용제",
        "advisory_vote": "12:0 찬성 (치료 공백 인정)",
        "safety": "QTc 연장 + 사망률 논란",
        "answer": True,
        "reason": "2016년 승인. 사후 사망률 시그널로 FDA가 재검토했으나 유지. 대안 부재가 결정적.",
        "ticker": "ACAD"
    }
]

# 세션 상태 초기화
if 'game_score' not in st.session_state:
    st.session_state.game_score = 0
if 'game_streak' not in st.session_state:
    st.session_state.game_streak = 0
if 'total_played' not in st.session_state:
    st.session_state.total_played = 0
if 'correct_count' not in st.session_state:  # ← 수정: 정답 개수 별도 추적
    st.session_state.correct_count = 0
if 'current_case' not in st.session_state:
    st.session_state.current_case = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'played_cases' not in st.session_state:  # ← 추가: 플레이한 케이스 추적
    st.session_state.played_cases = []

# 새 케이스 시작 (중복 방지)
if st.button("🎲 새로운 약물 케이스", use_container_width=True, type="primary"):
    # 아직 안 본 케이스만 필터링
    available_cases = [c for c in DRUG_CASES if c['name'] not in st.session_state.played_cases]
    
    # 모든 케이스를 다 본 경우 리셋
    if len(available_cases) == 0:
        st.session_state.played_cases = []
        available_cases = DRUG_CASES
        st.success("🎉 모든 케이스를 완료했습니다! 처음부터 다시 시작합니다.")
    
    st.session_state.current_case = random.choice(available_cases)
    st.session_state.played_cases.append(st.session_state.current_case['name'])
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
        st.markdown(f"**현재 점수**: {st.session_state.game_score}점")
        st.markdown(f"**연속 정답**: {st.session_state.game_streak}회")
        st.markdown(f"**진행 상황**: {len(st.session_state.played_cases)}/{len(DRUG_CASES)}")
        if st.session_state.total_played > 0:
            accuracy = (st.session_state.correct_count / st.session_state.total_played * 100)
            st.markdown(f"**정답률**: {accuracy:.1f}%")
    
    # 답변 버튼
    if not st.session_state.answered:
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("✅ 승인", use_container_width=True, type="primary"):
                st.session_state.answered = True
                st.session_state.total_played += 1
                
                if case['answer'] == True:
                    st.session_state.correct_count += 1  # ← 수정: 정답 카운트
                    bonus = 5 if st.session_state.game_streak >= 2 else 0
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
                    st.session_state.correct_count += 1  # ← 수정: 정답 카운트
                    bonus = 5 if st.session_state.game_streak >= 2 else 0
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
            # 아직 안 본 케이스만 필터링
            available_cases = [c for c in DRUG_CASES if c['name'] not in st.session_state.played_cases]
            
            # 모든 케이스를 다 본 경우 리셋
            if len(available_cases) == 0:
                st.session_state.played_cases = []
                available_cases = DRUG_CASES
                st.info("🎉 모든 케이스를 완료했습니다! 처음부터 다시 시작합니다.")
            
            st.session_state.current_case = random.choice(available_cases)
            st.session_state.played_cases.append(st.session_state.current_case['name'])
            st.session_state.answered = False
            st.rerun()

else:
    st.info("👆 위의 '새로운 약물 케이스' 버튼을 눌러 게임을 시작하세요!")
    
    # 게임 설명
    with st.expander("📖 게임 방법"):
        st.markdown("""
        ### 게임 규칙
        1. **실제 FDA 심사 케이스** 20개를 바탕으로 한 임상시험 데이터가 제공됩니다
        2. 제공된 정보를 보고 **승인 또는 반려**를 예측하세요
        3. 정답 시 **10점**, 3연속 정답 시 **보너스 +5점**
        4. **중복 없이** 모든 케이스를 한 번씩 풀 수 있습니다
        
        ### 주요 케이스
        - **Aduhelm**: 자문위원 0:10 반대했지만 승인
        - **Exondys 51**: 12명 데이터로 승인
        - **Opdivo 간암**: 타 적응증 성공해도 p=0.075로 반려
        - **Nuplazid**: 사망률 논란에도 대안 부재로 승인 유지
        
        ### 팁
        - **Surrogate endpoint**만 개선되고 임상적 benefit이 불명확하면 위험
        - **희귀질환**은 데이터가 부족해도 승인될 수 있음
        - **자문위원회 반대**를 뒤집고 승인된 케이스도 있음
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
        accuracy = (st.session_state.correct_count / st.session_state.total_played * 100)
        st.metric("🎯 정답률", f"{accuracy:.1f}%")
    else:
        st.metric("🎯 정답률", "0%")

if st.button("🔄 게임 리셋"):
    st.session_state.game_score = 0
    st.session_state.game_streak = 0
    st.session_state.total_played = 0
    st.session_state.correct_count = 0
    st.session_state.current_case = None
    st.session_state.answered = False
    st.session_state.played_cases = []
    st.rerun()

