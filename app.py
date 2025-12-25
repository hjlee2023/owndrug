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
import urllib.parse

st.markdown("---")
st.markdown("---")
st.header("🎮 FDA Drug Hunter: 승인 예측 게임")
st.caption("실제 FDA 심사 케이스를 바탕으로 당신의 규제 전문가 실력을 테스트하세요!")

# 실제 FDA 케이스 데이터베이스 (20개)
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
if 'correct_count' not in st.session_state:
    st.session_state.correct_count = 0
if 'current_case' not in st.session_state:
    st.session_state.current_case = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'played_cases' not in st.session_state:
    st.session_state.played_cases = []
if 'game_finished' not in st.session_state:
    st.session_state.game_finished = False

# 게임 종료 체크
if st.session_state.game_finished:
    st.balloons()
    
    st.success("### 🎉 게임 완료! 모든 FDA 케이스를 정복했습니다!")
    
    # 최종 결과
    accuracy = (st.session_state.correct_count / st.session_state.total_played * 100) if st.session_state.total_played > 0 else 0
    
    col_result1, col_result2, col_result3 = st.columns(3)
    with col_result1:
        st.metric("🏆 최종 점수", f"{st.session_state.game_score}점", 
                  delta=f"{st.session_state.game_score - st.session_state.total_played*10:+d}점 (보너스)" if st.session_state.game_score > st.session_state.total_played*10 else None)
    with col_result2:
        st.metric("🎯 정답률", f"{accuracy:.1f}%")
    with col_result3:
        st.metric("🔥 최고 연속 정답", st.session_state.game_streak if st.session_state.game_streak > 0 else "기록 없음")
    
    # 등급 판정
    st.markdown("---")
    if accuracy >= 90:
        grade = "FDA Commissioner"
        emoji = "🥇"
        message = "당신은 FDA 국장이 되기에 충분한 실력입니다. 자문위원회 반대도 뒤집을 수 있는 수준!"
    elif accuracy >= 80:
        grade = "Senior Reviewer"
        emoji = "🥈"
        message = "CDER의 시니어 심사관 수준입니다. Surrogate endpoint 평가에 능숙하시네요!"
    elif accuracy >= 70:
        grade = "Regulatory Affairs 전문가"
        emoji = "🥉"
        message = "제약사 RA 팀에서 일하기 충분한 실력입니다. NDA 준비 맡겨도 되겠어요!"
    elif accuracy >= 60:
        grade = "규제과학 학습자"
        emoji = "📚"
        message = "기본은 잡았지만 논란이 된 케이스들을 더 공부해보세요!"
    else:
        grade = "입문자"
        emoji = "🔰"
        message = "다시 도전해보세요! 희귀질환과 surrogate endpoint 개념을 복습하면 좋을 것 같아요."
    
    st.success(f"### {emoji} {grade} 급!")
    st.markdown(message)
    
    # 공유 링크 생성
    st.markdown("---")
    st.markdown("### 🔗 결과 공유하기")
    
    # 앱 URL (배포된 Streamlit 주소)
    app_url = "https://owndrug-aigmgmxuay3ntjszaxupmv.streamlit.app"
    
    # 공유 메시지 생성
    share_text = f"""🎮 FDA Drug Hunter 결과

{emoji} 등급: {grade}
🎯 정답률: {accuracy:.1f}%
🏆 점수: {st.session_state.game_score}점

나도 FDA 승인 예측 게임에 도전해보세요!
"""
    
    # URL 인코딩
    encoded_text = urllib.parse.quote(share_text)
    encoded_url = urllib.parse.quote(app_url)
    
    # 공유 버튼들
    col_share1, col_share2, col_share3 = st.columns(3)
    
    with col_share1:
        twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}"
        st.markdown(f"[🐦 트위터로 공유]({twitter_url})")
    
    with col_share2:
        # 카카오톡은 웹 공유 API 사용 (모바일에서만 작동)
        kakao_text = share_text.replace('\n', '%0A')
        st.markdown(f"💬 카카오톡으로 공유")
        st.caption("(모바일에서 복사 후 전송)")
    
    with col_share3:
        # 링크 복사용
        st.code(app_url, language=None)
        st.caption("링크 복사하기")
    
    # 텍스트 복사 영역
    with st.expander("📋 공유 메시지 복사"):
        st.text_area("아래 내용을 복사하세요", share_text + f"\n\n{app_url}", height=200)
    
    # 다시 시작 버튼
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 처음부터 다시 시작", use_container_width=True, type="primary"):
            st.session_state.game_score = 0
            st.session_state.game_streak = 0
            st.session_state.total_played = 0
            st.session_state.correct_count = 0
            st.session_state.current_case = None
            st.session_state.answered = False
            st.session_state.played_cases = []
            st.session_state.game_finished = False
            st.rerun()
    
    with col_btn2:
        if st.button("📰 뉴스 페이지로", use_container_width=True):
            st.session_state.game_score = 0
            st.session_state.game_streak = 0
            st.session_state.total_played = 0
            st.session_state.correct_count = 0
            st.session_state.current_case = None
            st.session_state.answered = False
            st.session_state.played_cases = []
            st.session_state.game_finished = False
            st.rerun()

else:
    # 새 케이스 시작 (중복 방지)
    if st.button("🎲 새로운 약물 케이스", use_container_width=True, type="primary"):
        # 아직 안 본 케이스만 필터링
        available_cases = [c for c in DRUG_CASES if c['name'] not in st.session_state.played_cases]
        
        # 모든 케이스를 다 본 경우
        if len(available_cases) == 0:
            st.session_state.game_finished = True
            st.rerun()
        
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
                        st.session_state.correct_count += 1
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
                        st.session_state.correct_count += 1
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
            
            # 다음 케이스 또는 결과 화면
            if st.button("➡️ 다음 케이스", use_container_width=True):
                # 아직 안 본 케이스만 필터링
                available_cases = [c for c in DRUG_CASES if c['name'] not in st.session_state.played_cases]
                
                # 모든 케이스를 다 본 경우 → 결과 화면
                if len(available_cases) == 0:
                    st.session_state.game_finished = True
                    st.rerun()
                
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
            4. **중복 없이** 모든 케이스를 한 번씩 풀면 **최종 결과 화면**이 나옵니다
            5. 결과를 **SNS로 공유**하여 친구들에게 도전장을 내밀 수 있습니다!
            
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
        st.session_state.game_finished = False
        st.rerun()

# ============================================
# 🎮 약사 피하기 게임 (PC + 모바일 지원)
# ============================================

import streamlit as st
import streamlit.components.v1 as components

def dodge_pharmacist_game():
    """약사 피하기 미니게임 - PC 키보드 + 모바일 터치 지원"""
    
    st.markdown("---")
    st.header("🎮 약사 피하기 게임")
    st.markdown("**PC:** ← → 방향키로 이동 | **모바일:** 화면 터치로 이동 | 💊 약을 먹으면 점수 +1 | 💣 부작용 폭탄 피하기!")
    
    # 게임 HTML/JavaScript 코드
    game_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                -webkit-tap-highlight-color: transparent;
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                user-select: none;
            }
            body {
                margin: 0;
                padding: 10px;
                display: flex;
                justify-content: center;
                align-items: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: 'Arial', sans-serif;
                overflow: hidden;
            }
            #gameContainer {
                text-align: center;
                max-width: 100%;
            }
            #gameCanvas {
                border: 4px solid white;
                border-radius: 10px;
                background: linear-gradient(180deg, #87CEEB 0%, #E0F6FF 100%);
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                display: block;
                margin: 0 auto;
                max-width: 100%;
                height: auto;
                touch-action: none;
            }
            #scoreBoard {
                background: rgba(255,255,255,0.9);
                padding: 8px 15px;
                border-radius: 10px;
                margin: 10px auto;
                max-width: 95%;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                overflow: hidden;
                word-wrap: break-word;
            }
            #score {
                font-size: 20px;
                font-weight: bold;
                color: #667eea;
                margin: 5px 0;
            }
            #rank {
                font-size: 16px;
                color: #764ba2;
                margin: 5px 0;
            }
            #gameOver {
                font-size: 22px;
                color: #ff4444;
                font-weight: bold;
                margin: 10px 0;
                display: none;
            }
            .button-container {
                margin: 10px 0;
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 10px;
            }
            .button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 25px;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                transition: transform 0.2s;
                touch-action: manipulation;
            }
            .button:active {
                transform: scale(0.95);
            }
            #controlHint {
                background: rgba(255,255,255,0.8);
                padding: 8px 15px;
                border-radius: 8px;
                margin: 10px auto;
                font-size: 14px;
                color: #333;
                max-width: 90%;
            }
            
            @media (max-width: 600px) {
                body {
                    padding: 5px;
                }
                #scoreBoard {
                    padding: 6px 10px;
                    margin: 5px auto;
                    max-width: 98%;
                }
                #score { 
                    font-size: 16px;
                    line-height: 1.3;
                }
                #rank { 
                    font-size: 13px;
                    line-height: 1.3;
                }
                #gameOver { 
                    font-size: 16px;
                    line-height: 1.3;
                }
                .button { 
                    padding: 8px 12px; 
                    font-size: 12px; 
                }
                #controlHint {
                    font-size: 12px;
                    padding: 6px 10px;
                    margin: 5px auto;
                }
                #gameCanvas {
                    border: 3px solid white;
                }
            }

            @media (max-width: 400px) {
                body {
                    padding: 3px;
                }
                #scoreBoard {
                    padding: 5px 8px;
                    margin: 3px auto;
                }
                #score { 
                    font-size: 14px;
                }
                #rank { 
                    font-size: 12px;
                }
                #gameOver { 
                    font-size: 14px;
                }
                .button { 
                    padding: 6px 10px; 
                    font-size: 11px; 
                }
                #controlHint {
                    font-size: 11px;
                    padding: 5px 8px;
                }
            }
        </style>
    </head>
    <body>
        <div id="gameContainer">
            <div id="scoreBoard">
                <div id="score">점수: 0</div>
                <div id="rank">직급: 약국 인턴</div>
                <div id="gameOver"></div>
            </div>
            <div id="controlHint">PC: ←→ 키보드 | 모바일: 화면 터치 👆</div>
            <canvas id="gameCanvas" width="400" height="600"></canvas>
            <div class="button-container">
                <button class="button" onclick="startGame()">🎮 새 게임</button>
                <button class="button" onclick="togglePause()">⏸️ 일시정지</button>
            </div>
        </div>

        <script>
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            
            // 캔버스 반응형 설정
            function resizeCanvas() {
                const container = document.getElementById('gameContainer');
                const maxWidth = Math.min(400, window.innerWidth - 40);
                const scale = maxWidth / 400;
                canvas.style.width = maxWidth + 'px';
                canvas.style.height = (600 * scale) + 'px';
            }
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);
            
            // 게임 상태
            let gameState = {
                player: {
                    x: canvas.width / 2 - 20,
                    y: canvas.height - 80,
                    width: 40,
                    height: 40,
                    speed: 7,
                    targetX: null // 터치 목표 위치
                },
                items: [],
                score: 0,
                gameOver: false,
                paused: false,
                frame: 0,
                spawnRate: 60,
                speed: 2,
                isMobile: false
            };
            
            // 모바일 감지
            gameState.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            
            // 키보드 입력 (PC)
            const keys = {};
            document.addEventListener('keydown', (e) => {
                keys[e.key] = true;
                e.preventDefault();
            });
            document.addEventListener('keyup', (e) => {
                keys[e.key] = false;
                e.preventDefault();
            });
            
            // 터치 입력 (모바일)
            let touchActive = false;
            
            canvas.addEventListener('touchstart', (e) => {
                e.preventDefault();
                touchActive = true;
                handleTouch(e);
            }, { passive: false });
            
            canvas.addEventListener('touchmove', (e) => {
                e.preventDefault();
                if (touchActive) {
                    handleTouch(e);
                }
            }, { passive: false });
            
            canvas.addEventListener('touchend', (e) => {
                e.preventDefault();
                touchActive = false;
                gameState.player.targetX = null;
            }, { passive: false });
            
            canvas.addEventListener('touchcancel', (e) => {
                e.preventDefault();
                touchActive = false;
                gameState.player.targetX = null;
            }, { passive: false });
            
            // 마우스 입력 (PC에서 클릭으로도 플레이 가능)
            canvas.addEventListener('mousedown', (e) => {
                touchActive = true;
                handleMouse(e);
            });
            
            canvas.addEventListener('mousemove', (e) => {
                if (touchActive) {
                    handleMouse(e);
                }
            });
            
            canvas.addEventListener('mouseup', (e) => {
                touchActive = false;
                gameState.player.targetX = null;
            });
            
            canvas.addEventListener('mouseleave', (e) => {
                touchActive = false;
                gameState.player.targetX = null;
            });
            
            function handleTouch(e) {
                if (gameState.gameOver || gameState.paused) return;
                
                const rect = canvas.getBoundingClientRect();
                const scaleX = canvas.width / rect.width;
                const touch = e.touches[0];
                const x = (touch.clientX - rect.left) * scaleX;
                
                gameState.player.targetX = x - gameState.player.width / 2;
            }
            
            function handleMouse(e) {
                if (gameState.gameOver || gameState.paused) return;
                
                const rect = canvas.getBoundingClientRect();
                const scaleX = canvas.width / rect.width;
                const x = (e.clientX - rect.left) * scaleX;
                
                gameState.player.targetX = x - gameState.player.width / 2;
            }
            
            // 직급 시스템
            function getRank(score) {
                if (score < 10) return '약대생';
                if (score < 25) return '신입 약사';
                if (score < 50) return '경력 약사';
                if (score < 100) return '약국장';
                if (score < 150) return '약무이사';
                if (score < 200) return 'FDA 심사관';
                if (score < 300) return 'FDA 부국장';
                return 'FDA 국장 🏆';
            }
            
            // 아이템 생성
            function createItem() {
                const isGood = Math.random() > 0.25;
                return {
                    x: Math.random() * (canvas.width - 30),
                    y: -30,
                    width: 30,
                    height: 30,
                    type: isGood ? 'pill' : 'bomb',
                    emoji: isGood ? '💊' : '💣',
                    speed: gameState.speed + Math.random() * 2
                };
            }
            
            // 플레이어 그리기
            function drawPlayer() {
                ctx.font = '40px Arial';
                ctx.fillText('🏃', gameState.player.x, gameState.player.y + 35);
            }
            
            // 아이템 그리기
            function drawItems() {
                gameState.items.forEach(item => {
                    ctx.font = '30px Arial';
                    ctx.fillText(item.emoji, item.x, item.y + 25);
                });
            }
            
            // 충돌 감지
            function checkCollision(player, item) {
                return player.x < item.x + item.width &&
                       player.x + player.width > item.x &&
                       player.y < item.y + item.height &&
                       player.y + player.height > item.y;
            }
            
            // 게임 업데이트
            function update() {
                if (gameState.gameOver || gameState.paused) return;
                
                gameState.frame++;
                
                // 플레이어 이동 - 키보드
                if ((keys['ArrowLeft'] || keys['a'] || keys['A']) && gameState.player.x > 0) {
                    gameState.player.x -= gameState.player.speed;
                }
                if ((keys['ArrowRight'] || keys['d'] || keys['D']) && gameState.player.x < canvas.width - gameState.player.width) {
                    gameState.player.x += gameState.player.speed;
                }
                
                // 플레이어 이동 - 터치/마우스 (부드러운 이동)
                if (gameState.player.targetX !== null) {
                    const dx = gameState.player.targetX - gameState.player.x;
                    const moveSpeed = Math.min(Math.abs(dx), gameState.player.speed);
                    
                    if (Math.abs(dx) > 2) {
                        if (dx > 0) {
                            gameState.player.x += moveSpeed;
                        } else {
                            gameState.player.x -= moveSpeed;
                        }
                    }
                    
                    // 경계 체크
                    gameState.player.x = Math.max(0, Math.min(canvas.width - gameState.player.width, gameState.player.x));
                }
                
                // 아이템 생성
                if (gameState.frame % gameState.spawnRate === 0) {
                    gameState.items.push(createItem());
                }
                
                // 난이도 증가
                if (gameState.score > 0 && gameState.score % 20 === 0) {
                    gameState.speed = 2 + gameState.score / 50;
                    gameState.spawnRate = Math.max(10, 60 - gameState.score / 5); 
                }
                
                // 아이템 업데이트
                gameState.items = gameState.items.filter(item => {
                    item.y += item.speed;
                    
                    // 충돌 체크
                    if (checkCollision(gameState.player, item)) {
                        if (item.type === 'pill') {
                            gameState.score++;
                            // 점수 획득 효과
                            playScoreEffect(item.x, item.y);
                            return false;
                        } else {
                            // 게임 오버
                            gameState.gameOver = true;
                            document.getElementById('gameOver').style.display = 'block';
                            document.getElementById('gameOver').textContent = '게임 오버! 💥 부작용 발생!';
                            return false;
                        }
                    }
                    
                    return item.y < canvas.height + 50;
                });
                
                // 스코어 업데이트
                document.getElementById('score').textContent = `점수: ${gameState.score}`;
                document.getElementById('rank').textContent = `직급: ${getRank(gameState.score)}`;
            }
            
            // 점수 획득 효과
            function playScoreEffect(x, y) {
                // 간단한 +1 텍스트 효과 (선택사항)
            }
            
            // 게임 렌더링
            function render() {
                // 배경
                const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
                gradient.addColorStop(0, '#87CEEB');
                gradient.addColorStop(1, '#E0F6FF');
                ctx.fillStyle = gradient;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // 구름 (애니메이션)
                ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
                const cloud1Y = 100 + (gameState.frame % 200);
                ctx.beginPath();
                ctx.arc(80, cloud1Y, 30, 0, Math.PI * 2);
                ctx.arc(120, cloud1Y - 5, 40, 0, Math.PI * 2);
                ctx.arc(160, cloud1Y, 30, 0, Math.PI * 2);
                ctx.fill();
                
                const cloud2Y = 250 + (gameState.frame % 150);
                ctx.beginPath();
                ctx.arc(280, cloud2Y, 35, 0, Math.PI * 2);
                ctx.arc(320, cloud2Y - 5, 45, 0, Math.PI * 2);
                ctx.arc(360, cloud2Y, 35, 0, Math.PI * 2);
                ctx.fill();
                
                // 게임 요소
                drawItems();
                drawPlayer();
                
                // 일시정지
                if (gameState.paused) {
                    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 40px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText('⏸️ 일시정지', canvas.width / 2, canvas.height / 2);
                    ctx.textAlign = 'left';
                }
            }
            
            // 게임 루프
            function gameLoop() {
                update();
                render();
                requestAnimationFrame(gameLoop);
            }
            
            // 게임 시작
            function startGame() {
                gameState = {
                    player: {
                        x: canvas.width / 2 - 20,
                        y: canvas.height - 80,
                        width: 40,
                        height: 40,
                        speed: 7,
                        targetX: null
                    },
                    items: [],
                    score: 0,
                    gameOver: false,
                    paused: false,
                    frame: 0,
                    spawnRate: 60,
                    speed: 2,
                    isMobile: gameState.isMobile
                };
                document.getElementById('gameOver').style.display = 'none';
                document.getElementById('score').textContent = '점수: 0';
                document.getElementById('rank').textContent = '직급: 약대생';
            }
            
            // 일시정지
            function togglePause() {
                if (!gameState.gameOver) {
                    gameState.paused = !gameState.paused;
                }
            }
            
            // 게임 시작
            startGame();
            gameLoop();
        </script>
    </body>
    </html>
    """
    
    # HTML 컴포넌트 렌더링
    components.html(game_html, height=850, scrolling=False)
    
    # 게임 설명
    with st.expander("🎯 게임 가이드"):
        st.markdown("""
        ### 게임 방법
        - **목표**: 하늘에서 떨어지는 약(💊)을 최대한 많이 먹으세요!
        - **조작 (PC)**: 키보드 ← → 방향키 또는 A, D 키로 좌우 이동
        - **조작 (모바일)**: 화면을 터치하면 캐릭터가 터치한 위치로 이동
        - **조작 (PC 마우스)**: 마우스를 클릭한 채로 드래그해도 이동 가능
        - **주의**: 💣 부작용 폭탄에 맞으면 게임 오버!
        
        ### 모바일 팁
        - 화면 아무 곳이나 터치하면 캐릭터가 그 위치로 부드럽게 이동합니다
        - 손가락을 계속 움직이면 캐릭터도 따라 움직입니다
        - PC에서도 마우스로 클릭&드래그 가능!
        
        **팁**: 욕심내지 말고 안전하게 플레이하세요! 💊
        """)

# 게임 실행 (app.py 맨 뒤에 추가)
if __name__ == "__main__":
    dodge_pharmacist_game()

# ============================================
# 💊 약물 배틀 게임
# ============================================

import streamlit as st
import streamlit.components.v1 as components

def drug_battle_game():
    """약물 배틀 게임"""
    
    st.markdown("---")
    st.header("💊 약물 배틀 아레나")
    st.markdown("**약물을 선택해서 질병과 전투하세요!**")
    
    # 게임 HTML/JavaScript 코드
    game_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {
                -webkit-tap-highlight-color: transparent;
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                user-select: none;
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                margin: 0;
                padding: 10px;
                background: linear-gradient(135deg, #1a237e 0%, #311b92 100%);
                font-family: 'Courier New', monospace;
                overflow-x: hidden;
            }
            #gameContainer {
                max-width: 700px;
                margin: 0 auto;
            }
            #battleScreen {
                background: linear-gradient(180deg, #87ceeb 0%, #98d8c8 50%, #8bc34a 100%);
                border: 6px solid #fff;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.5);
                position: relative;
                overflow: hidden;
            }
            .character-area {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 20px 0;
                min-height: 200px;
            }
            .character {
                text-align: center;
                position: relative;
            }
            .character-sprite {
                font-size: 100px;
                animation: float 2s ease-in-out infinite;
                filter: drop-shadow(0 5px 10px rgba(0,0,0,0.3));
            }
            .player-sprite {
                animation-delay: 0s;
            }
            .enemy-sprite {
                animation-delay: 1s;
            }
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
            }
            .shake {
                animation: shake 0.5s;
            }
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-10px); }
                75% { transform: translateX(10px); }
            }
            .attack-animation {
                animation: attackFlash 0.5s;
            }
            @keyframes attackFlash {
                0%, 100% { filter: brightness(1); }
                50% { filter: brightness(2) drop-shadow(0 0 20px yellow); }
            }
            .stat-box {
                background: white;
                border: 4px solid #333;
                border-radius: 10px;
                padding: 10px 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                min-width: 200px;
            }
            .stat-name {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }
            .stat-level {
                font-size: 12px;
                color: #666;
                margin-bottom: 8px;
            }
            .hp-bar-container {
                background: #ddd;
                border: 2px solid #333;
                border-radius: 10px;
                height: 20px;
                overflow: hidden;
                position: relative;
            }
            .hp-bar {
                background: linear-gradient(90deg, #4caf50 0%, #8bc34a 100%);
                height: 100%;
                transition: width 0.5s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 11px;
                font-weight: bold;
                color: white;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            }
            .hp-bar.low {
                background: linear-gradient(90deg, #ff9800 0%, #ffc107 100%);
            }
            .hp-bar.critical {
                background: linear-gradient(90deg, #f44336 0%, #ff5722 100%);
                animation: pulse 0.5s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            #messageBox {
                background: white;
                border: 4px solid #333;
                border-radius: 10px;
                padding: 15px;
                margin: 20px 0;
                min-height: 80px;
                font-size: 16px;
                color: #333;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                position: relative;
            }
            #messageText {
                line-height: 1.5;
            }
            #actionMenu {
                background: white;
                border: 4px solid #333;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            }
            .action-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }
            .action-btn {
                background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%);
                border: 3px solid #fff;
                border-radius: 10px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                color: white;
                cursor: pointer;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                transition: transform 0.1s;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            }
            .action-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.3);
            }
            .action-btn:active {
                transform: translateY(0);
            }
            .action-btn.attack {
                background: linear-gradient(135deg, #ef5350 0%, #c62828 100%);
            }
            .action-btn.heal {
                background: linear-gradient(135deg, #66bb6a 0%, #388e3c 100%);
            }
            .action-btn.special {
                background: linear-gradient(135deg, #ffa726 0%, #f57c00 100%);
            }
            .action-btn.run {
                background: linear-gradient(135deg, #78909c 0%, #455a64 100%);
            }
            .action-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            #gameOverModal {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0,0,0,0.95);
                border: 6px solid #ffd700;
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                display: none;
                z-index: 1000;
                max-width: 90%;
                box-shadow: 0 0 50px rgba(255,215,0,0.5);
            }
            #gameOverModal h2 {
                color: #ffd700;
                font-size: 36px;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
            #gameOverModal p {
                color: white;
                font-size: 18px;
                margin: 10px 0;
            }
            .button {
                background: linear-gradient(135deg, #ffd700 0%, #ffa000 100%);
                color: #333;
                border: 3px solid white;
                padding: 12px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 25px;
                cursor: pointer;
                margin: 10px 5px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                transition: transform 0.2s;
            }
            .button:active {
                transform: scale(0.95);
            }
            .damage-text {
                position: absolute;
                font-size: 36px;
                font-weight: bold;
                color: #f44336;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                animation: damageFloat 1s ease-out forwards;
                pointer-events: none;
                z-index: 100;
            }
            @keyframes damageFloat {
                0% { transform: translateY(0) scale(1); opacity: 1; }
                100% { transform: translateY(-50px) scale(1.5); opacity: 0; }
            }
            
            @media (max-width: 600px) {
                .character-sprite { font-size: 70px; }
                .stat-box { min-width: 150px; padding: 8px 10px; }
                .stat-name { font-size: 14px; }
                .action-btn { padding: 12px; font-size: 14px; }
                #messageBox { font-size: 14px; min-height: 60px; }
            }
        </style>
    </head>
    <body>
        <div id="gameContainer">
            <div id="battleScreen">
                <div class="character-area">
                    <div class="character player">
                        <div class="stat-box">
                            <div class="stat-name" id="playerName">아스피린</div>
                            <div class="stat-level">Lv. <span id="playerLevel">5</span></div>
                            <div class="hp-bar-container">
                                <div class="hp-bar" id="playerHP">
                                    <span id="playerHPText">100/100</span>
                                </div>
                            </div>
                        </div>
                        <div class="character-sprite player-sprite" id="playerSprite">💊</div>
                    </div>
                    
                    <div class="character enemy">
                        <div class="stat-box">
                            <div class="stat-name" id="enemyName">고혈압</div>
                            <div class="stat-level">Lv. <span id="enemyLevel">5</span></div>
                            <div class="hp-bar-container">
                                <div class="hp-bar" id="enemyHP">
                                    <span id="enemyHPText">100/100</span>
                                </div>
                            </div>
                        </div>
                        <div class="character-sprite enemy-sprite" id="enemySprite">😰</div>
                    </div>
                </div>
                
                <div id="messageBox">
                    <div id="messageText">야생의 질병이 나타났다!</div>
                </div>
                
                <div id="actionMenu">
                    <div class="action-grid">
                        <button class="action-btn attack" onclick="playerAction('attack')">
                            ⚔️ 공격
                        </button>
                        <button class="action-btn special" onclick="playerAction('special')">
                            ✨ 특수 공격
                        </button>
                        <button class="action-btn heal" onclick="playerAction('heal')">
                            ❤️ 회복
                        </button>
                        <button class="action-btn run" onclick="playerAction('run')">
                            🏃 도망
                        </button>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 15px;">
                <button class="button" onclick="startNewBattle()">🎮 새 전투</button>
                <button class="button" onclick="nextEnemy()">⏭️ 다음 적</button>
            </div>
            
            <div id="gameOverModal">
                <h2 id="gameOverTitle">🏆 승리!</h2>
                <p id="gameOverText"></p>
                <button class="button" onclick="nextEnemy()">다음 전투 ➡️</button>
                <button class="button" onclick="startNewBattle()">처음부터 🔄</button>
            </div>
        </div>

        <script>
            // 약물 데이터
            const drugs = [
                { name: '아스피린', emoji: '💊', hp: 100, attack: 15, special: 25, heal: 20 },
                { name: '페니실린', emoji: '💉', hp: 120, attack: 20, special: 30, heal: 15 },
                { name: '인슐린', emoji: '💙', hp: 110, attack: 18, special: 28, heal: 18 },
                { name: '모르핀', emoji: '💜', hp: 90, attack: 12, special: 35, heal: 25 }
            ];
            
            // 질병 데이터
            const diseases = [
                { name: '고혈압', emoji: '😰', hp: 80, attack: 12 },
                { name: '당뇨병', emoji: '🤒', hp: 100, attack: 15 },
                { name: '감염', emoji: '🤢', hp: 90, attack: 18 },
                { name: '통증', emoji: '😣', hp: 70, attack: 10 },
                { name: '우울증', emoji: '😔', hp: 95, attack: 14 },
                { name: '암', emoji: '😱', hp: 150, attack: 25 }
            ];
            
            // 게임 상태
            let gameState = {
                player: null,
                enemy: null,
                playerMaxHP: 100,
                enemyMaxHP: 100,
                level: 1,
                wins: 0,
                isPlayerTurn: true,
                inBattle: true
            };
            
            // 게임 초기화
            function initGame() {
                const randomDrug = drugs[Math.floor(Math.random() * drugs.length)];
                const randomDisease = diseases[Math.floor(Math.random() * diseases.length)];
                
                gameState.player = { ...randomDrug, currentHP: randomDrug.hp };
                gameState.enemy = { ...randomDisease, currentHP: randomDisease.hp };
                gameState.playerMaxHP = randomDrug.hp;
                gameState.enemyMaxHP = randomDisease.hp;
                gameState.isPlayerTurn = true;
                gameState.inBattle = true;
                
                updateUI();
                showMessage(`야생의 ${gameState.enemy.name}이(가) 나타났다!`);
            }
            
            // UI 업데이트
            function updateUI() {
                // 플레이어
                document.getElementById('playerName').textContent = gameState.player.name;
                document.getElementById('playerLevel').textContent = gameState.level;
                document.getElementById('playerSprite').textContent = gameState.player.emoji;
                updateHPBar('player');
                
                // 적
                document.getElementById('enemyName').textContent = gameState.enemy.name;
                document.getElementById('enemyLevel').textContent = gameState.level;
                document.getElementById('enemySprite').textContent = gameState.enemy.emoji;
                updateHPBar('enemy');
            }
            
            // HP 바 업데이트
            function updateHPBar(target) {
                const isPlayer = target === 'player';
                const character = isPlayer ? gameState.player : gameState.enemy;
                const maxHP = isPlayer ? gameState.playerMaxHP : gameState.enemyMaxHP;
                const hpBar = document.getElementById(isPlayer ? 'playerHP' : 'enemyHP');
                const hpText = document.getElementById(isPlayer ? 'playerHPText' : 'enemyHPText');
                
                const currentHP = Math.max(0, character.currentHP);
                const percentage = (currentHP / maxHP) * 100;
                
                hpBar.style.width = percentage + '%';
                hpText.textContent = `${currentHP}/${maxHP}`;
                
                // HP 바 색상 변경
                hpBar.classList.remove('low', 'critical');
                if (percentage <= 25) {
                    hpBar.classList.add('critical');
                } else if (percentage <= 50) {
                    hpBar.classList.add('low');
                }
            }
            
            // 메시지 표시
            function showMessage(text) {
                document.getElementById('messageText').textContent = text;
            }
            
            // 플레이어 행동
            async function playerAction(action) {
                if (!gameState.inBattle || !gameState.isPlayerTurn) return;
                
                disableButtons();
                
                switch(action) {
                    case 'attack':
                        await performAttack(true, gameState.player.attack);
                        break;
                    case 'special':
                        await performAttack(true, gameState.player.special, true);
                        break;
                    case 'heal':
                        await performHeal();
                        break;
                    case 'run':
                        showMessage('도망칠 수 없다!');
                        await sleep(1500);
                        break;
                }
                
                // 적이 죽었는지 확인
                if (gameState.enemy.currentHP <= 0) {
                    await enemyDefeated();
                    return;
                }
                
                // 적 턴
                gameState.isPlayerTurn = false;
                await sleep(1000);
                await enemyTurn();
                
                gameState.isPlayerTurn = true;
                enableButtons();
            }
            
            // 공격 수행
            async function performAttack(isPlayer, damage, isSpecial = false) {
                const attacker = isPlayer ? gameState.player : gameState.enemy;
                const defender = isPlayer ? gameState.enemy : gameState.player;
                const attackerName = attacker.name;
                const defenderSprite = document.getElementById(isPlayer ? 'enemySprite' : 'playerSprite');
                
                const actualDamage = Math.floor(damage * (0.85 + Math.random() * 0.3));
                defender.currentHP -= actualDamage;
                
                // 애니메이션
                defenderSprite.classList.add('shake', 'attack-animation');
                showDamageText(actualDamage, isPlayer);
                
                const attackType = isSpecial ? '특수 공격을' : '공격을';
                showMessage(`${attackerName}의 ${attackType} 사용했다!`);
                
                await sleep(500);
                updateHPBar(isPlayer ? 'enemy' : 'player');
                
                await sleep(500);
                defenderSprite.classList.remove('shake', 'attack-animation');
            }
            
            // 회복
            async function performHeal() {
                const healAmount = gameState.player.heal;
                const oldHP = gameState.player.currentHP;
                gameState.player.currentHP = Math.min(gameState.playerMaxHP, gameState.player.currentHP + healAmount);
                const actualHeal = gameState.player.currentHP - oldHP;
                
                showMessage(`${gameState.player.name}은(는) HP를 ${actualHeal} 회복했다!`);
                
                const playerSprite = document.getElementById('playerSprite');
                playerSprite.style.filter = 'brightness(1.5) drop-shadow(0 0 20px #4caf50)';
                
                await sleep(500);
                updateHPBar('player');
                await sleep(500);
                
                playerSprite.style.filter = '';
            }
            
            // 적 턴
            async function enemyTurn() {
                await performAttack(false, gameState.enemy.attack);
                
                // 플레이어가 죽었는지 확인
                if (gameState.player.currentHP <= 0) {
                    await playerDefeated();
                }
            }
            
            // 데미지 텍스트
            function showDamageText(damage, isPlayerAttacking) {
                const battleScreen = document.getElementById('battleScreen');
                const damageText = document.createElement('div');
                damageText.className = 'damage-text';
                damageText.textContent = `-${damage}`;
                damageText.style.left = isPlayerAttacking ? '70%' : '30%';
                damageText.style.top = '40%';
                
                battleScreen.appendChild(damageText);
                
                setTimeout(() => {
                    damageText.remove();
                }, 1000);
            }
            
            // 적 처치
            async function enemyDefeated() {
                gameState.inBattle = false;
                showMessage(`${gameState.enemy.name}을(를) 물리쳤다!`);
                
                const enemySprite = document.getElementById('enemySprite');
                enemySprite.style.opacity = '0';
                enemySprite.style.transform = 'scale(0)';
                enemySprite.style.transition = 'all 0.5s';
                
                await sleep(1500);
                
                gameState.wins++;
                
                document.getElementById('gameOverTitle').textContent = '🏆 승리!';
                document.getElementById('gameOverText').innerHTML = `
                    ${gameState.enemy.name}을(를) 물리쳤습니다!<br>
                    연속 승리: ${gameState.wins}
                `;
                document.getElementById('gameOverModal').style.display = 'block';
            }
            
            // 플레이어 패배
            async function playerDefeated() {
                gameState.inBattle = false;
                showMessage(`${gameState.player.name}은(는) 쓰러졌다...`);
                
                const playerSprite = document.getElementById('playerSprite');
                playerSprite.style.opacity = '0.3';
                
                await sleep(1500);
                
                document.getElementById('gameOverTitle').textContent = '💔 패배...';
                document.getElementById('gameOverText').innerHTML = `
                    ${gameState.enemy.name}에게 패배했습니다...<br>
                    연속 승리: ${gameState.wins}
                `;
                document.getElementById('gameOverModal').style.display = 'block';
            }
            
            // 다음 적
            function nextEnemy() {
                gameState.level++;
                const randomDisease = diseases[Math.floor(Math.random() * diseases.length)];
                gameState.enemy = { 
                    ...randomDisease, 
                    currentHP: randomDisease.hp + (gameState.level * 10)
                };
                gameState.enemyMaxHP = gameState.enemy.currentHP;
                
                // 플레이어 HP 일부 회복
                gameState.player.currentHP = Math.min(
                    gameState.playerMaxHP, 
                    gameState.player.currentHP + 30
                );
                
                gameState.isPlayerTurn = true;
                gameState.inBattle = true;
                
                document.getElementById('gameOverModal').style.display = 'none';
                document.getElementById('enemySprite').style = '';
                document.getElementById('playerSprite').style = '';
                
                updateUI();
                showMessage(`야생의 ${gameState.enemy.name}이(가) 나타났다!`);
                enableButtons();
            }
            
            // 새 전투
            function startNewBattle() {
                gameState.level = 1;
                gameState.wins = 0;
                document.getElementById('gameOverModal').style.display = 'none';
                document.getElementById('enemySprite').style = '';
                document.getElementById('playerSprite').style = '';
                initGame();
                enableButtons();
            }
            
            // 버튼 제어
            function disableButtons() {
                document.querySelectorAll('.action-btn').forEach(btn => {
                    btn.disabled = true;
                });
            }
            
            function enableButtons() {
                document.querySelectorAll('.action-btn').forEach(btn => {
                    btn.disabled = false;
                });
            }
            
            // Sleep 함수
            function sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }
            
            // 게임 시작
            initGame();
        </script>
    </body>
    </html>
    """
    
    # HTML 컴포넌트 렌더링
    components.html(game_html, height=750, scrolling=False)
    
    # 게임 설명
    with st.expander("🎯 게임 가이드"):
        st.markdown("""
        ### 게임 방법
        **목표**: 약물을 조작해서 질병을 물리치세요!
        
        ### 전투 시스템
        - 턴제 배틀
        - 플레이어 → 적 순서로 번갈아가며 공격
        - HP가 0이 되면 게임 오버!
        
        ### 행동 옵션
        - **⚔️ 공격**: 기본 공격 (중간 데미지)
        - **✨ 특수 공격**: 강력한 공격 (높은 데미지)
        - **❤️ 회복**: HP 회복
        - **🏃 도망**: 도망칠 수 없습니다!
        
        ### 약물 캐릭터
        - **💊 아스피린**: 균형잡힌 스탯
        - **💉 페니실린**: 높은 HP와 공격력
        - **💙 인슐린**: 중간 올라운더
        - **💜 모르핀**: 낮은 HP, 강력한 특수 공격
        
        ### 질병 적
        - **😰 고혈압**: 약한 적
        - **🤒 당뇨병**: 중간 난이도
        - **🤢 감염**: 높은 공격력
        - **😣 통증**: 낮은 HP
        - **😔 우울증**: 균형잡힌 적
        - **😱 암**: 보스급 적 (높은 HP)
        
        ### 난이도 시스템
        - 승리할 때마다 레벨 상승
        - 레벨이 오를수록 적의 HP 증가
        - 전투 승리 시 HP 30 회복
        
        ### HP 바 색상
        - **초록색**: 건강 (50% 이상)
        - **주황색**: 주의 (25-50%)
        - **빨간색**: 위험 (25% 이하, 깜빡임)
        
        ### 팁
        - 특수 공격은 데미지가 높지만 적절한 타이밍에 사용
        - HP가 낮을 때는 회복 우선
        - 연속 승리 기록에 도전하세요!
        
        **약물의 힘으로 질병을 물리치세요!** 💊⚔️
        """)

# 게임 실행 (app.py에 추가)
if __name__ == "__main__":
    drug_battle_game()
