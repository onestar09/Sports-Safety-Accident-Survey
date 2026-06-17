import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. 페이지 설정 및 제목
st.set_page_config(
    page_title="2024 스포츠 안전사고 실태조사 대시보드",
    page_icon="⛑️",
    layout="wide"
)

# 2. 데이터 로드 및 인코딩 방어 코드
@st.cache_data
def load_data():
    file_path = "2024_스포츠_안전사고_실태조사_체육인.csv"
    try:
        # 데이터의 진짜 컬럼이 있는 header=1로 읽어옵니다.
        df = pd.read_csv(file_path, header=1)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, header=1, encoding='cp949')
    
    # 컬럼명 양끝 공백 제거
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ 데이터를 불러오지 못했습니다. 파일명과 대소문자, 확장자를 확인해주세요. (오류: {e})")
    st.stop()

# ==============================================================================
# [최종 검증] 데이터 구조 맞춤형 컬럼 변수 매핑
# ==============================================================================
sport_column = "참여스포츠및 종목"

# 부상 여부 컬럼 매핑 자동 추적 코드
injury_exp_col = None
for col in df.columns:
    if "부상" in col and "경험" in col:
        injury_exp_col = col
        break
if not injury_exp_col:
    injury_exp_col = "스포츠 활동 중 부상 경험" if "스포츠 활동 중 부상 경험" in df.columns else df.columns[10]

# ==============================================================================
# 3. 사이드바 종목 필터
# ==============================================================================
st.sidebar.title("🔍 대시보드 필터")
st.sidebar.markdown("원하는 스포츠 종목을 선택하세요.")

if sport_column in df.columns:
    # 결측치 제외 및 문자열 변환 후 고유 목록 생성
    sports_list = ["전체 종목"] + sorted(df[sport_column].dropna().astype(str).unique().tolist())
else:
    st.error(f"❌ 데이터에서 '{sport_column}' 컬럼을 찾을 수 없습니다.")
    st.stop()

selected_sport = st.sidebar.selectbox("🎯 스포츠 종목 선택", sports_list)

# 데이터 필터링 규칙
if selected_sport == "전체 종목":
    filtered_df = df
else:
    filtered_df = df[df[sport_column].astype(str) == selected_sport]

# ==============================================================================
# 4. 메인 UI 화면 구성
# ==============================================================================
st.title("⛑️ 스포츠 안전사고 실태조사 대시보드")
st.markdown(f"**📊 분석 대상 그룹:** `{selected_sport}`")
st.write("---")

# KPI 핵심 메트릭스 계산
total_res = len(filtered_df)

# 부상 경험 유무 조건 검사 (문자열 '1', '있음', '유' 등 다각도 탐색)
injury_condition = filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험|유|예', na=False)
injured_res = len(filtered_df[injury_condition])
rate = (injured_res / total_res * 100) if total_res > 0 else 0.0

col1, col2, col3 = st.columns(3)
col1.metric(label="📊 총 응답자 수", value=f"{total_res:,} 명")
col2.metric(label="🤕 부상 경험자 수", value=f"{injured_res:,} 명")
col3.metric(label="📈 평균 부상률", value=f"{rate:.1f} %")

st.write("")
st.markdown("### 📊 부상 사고 패턴 상세 분석")

# 실제로 부상을 당한 사람의 데이터만 슬라이싱하여 통계 산출
injury_data = filtered_df[injury_condition]

if len(injury_data) == 0:
    st.info("ℹ️ 현재 선택된 스포츠 그룹에는 부상 데이터 통계가 존재하지 않습니다.")
else:
    chart_col1, chart_col2 = st.columns(2)
    
    # --- [좌측: 부상 시간대 분석] ---
    with chart_col1:
        st.subheader("⏰ 부상 발생 시간대 분포")
        
        # '시간' 키워드를 포함하는 컬럼 탐색 및 동적 정제
        time_cols = [c for c in df.columns if "시간" in c or "시각" in c]
        
        if time_cols:
            # 설문조사 상 부상 분석에 가장 적합한 핵심 시간 컬럼 매핑
            target_time = time_cols[-1] 
            t_counts = injury_data[target_time].value_counts().reset_index()
            t_counts.columns = ['시간대', '부상 건수']
            
            # 코드 데이터 일치화 가공 및 매핑
            time_map = {
                '1': '새벽 (00시~06시)', '2': '오전 (06시~12시)', 
                '3': '오후 (12시~18시)', '4': '야간 (18시~24시)',
                1: '새벽 (00시~06시)', 2: '오전 (06시~12시)', 
                3: '오후 (12시~18시)', 4: '야간 (18시~24시)'
            }
            t_counts['시간대'] = t_counts['시간대'].replace(time_map).astype(str)
            
            fig_time = px.bar(
                t_counts.head(10), 
                x='시간대', 
                y='부상 건수', 
                text='부상 건수',
                color='부상 건수', 
                color_continuous_scale='Reds'
            )
            fig_time.update_traces(texttemplate='%{text}건', textposition='outside')
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("💡 데이터셋 내에서 부상 시간대 관련 항목을 로드하지 못했습니다.")

    # --- [우측: 부상 장소 분석] ---
    with chart_col2:
        st.subheader("📍 부상 발생 장소 TOP 10")
        
        # '장소' 또는 '시설' 키워드를 포함하는 컬럼 탐색
        place_cols = [c for c in df.columns if "장소" in c or "시설" in c]
        
        if place_cols:
            target_place = place_cols[0]
            p_counts = injury_data[target_place].value_counts().reset_index()
            p_counts.columns = ['장소/시설', '부상 건수']
            
            # 장소 코드값 명칭 치환용 가공 사전 적용
            place_map = {
                '1': '공공 체육시설', '2': '민간 체육시설', '3': '학교 체육시설', 
                '4': '기타/자연 환경', 1: '공공 체육시설', 2: '민간 체육시설', 
                3: '학교 체육시설', 4: '기타/자연 환경'
            }
            p_counts['장소/시설'] = p_counts['장소/시설'].replace(place_map).astype(str)
            
            fig_place = px.pie(
                p_counts.head(10), 
                values='부상 건수', 
                names='장소/시설', 
                hole=0.4, 
                color_discrete_sequence=px.colors.sequential.YlOrRd_r
            )
            fig_place.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_place, use_container_width=True)
        else:
            st.info("💡 데이터셋 내에서 부상 장소 관련 항목을 로드하지 못했습니다.")

# 5. 데이터 원본 검증 테이블 하단 배치
st.write("---")
if st.checkbox("📁 [최종 검증용] 필터링된 원본 데이터 셋 보기"):
    st.dataframe(filtered_df.head(50))
