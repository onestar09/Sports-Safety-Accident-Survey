import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================================================================
# 1. 페이지 기본 레이아웃 및 디자인 설정
# ==============================================================================
st.set_page_config(
    page_title="2024 스포츠 안전사고 실태조사 대시보드",
    page_icon="⛑️",
    layout="wide"
)

# ==============================================================================
# 2. 안전한 데이터 로딩 및 클렌징 함수 정의
# ==============================================================================
@st.cache_data
def load_data():
    # 데이터 파일의 실제 시작이 2번째 줄(인덱스 1)이므로 header=1 설정
    try:
        df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=1)
    except UnicodeDecodeError:
        df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=1, encoding='cp949')
    
    # [핵심 수정] 원본 데이터 컬럼명 내에 들어있는 모든 줄바꿈(\n, \r)과 좌우 공백을 제거하여 
    # 프로그램이 '참여스포츠 및 종목' 텍스트를 정확하게 찾을 수 있도록 정제합니다.
    df.columns = df.columns.str.replace(r'[\r\n\t]+', '', regex=True).str.strip()
    return df

# 데이터 로드 실행
try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ 데이터 파일을 로드하지 못했습니다. 파일명과 위치를 확인해 주세요. (오류: {e})")
    st.stop()

# ==============================================================================
# 3. 사이드바 컨트롤러 (종목 필터링)
# ==============================================================================
st.sidebar.title("🔍 대시보드 필터")
st.sidebar.markdown("원하는 스포츠 종목을 선택하여 분석 결과를 확인하세요.")

# 완벽하게 정제된 컬럼명을 변수로 지정합니다.
sport_column = "참여스포츠 및 종목"

if sport_column in df.columns:
    # 빈 값(NaN)을 제거하고 가나다순으로 정렬하여 드롭다운 리스트 생성
    sports_list = ["전체 종목"] + sorted(df[sport_column].dropna().unique().tolist())
else:
    st.error(f"❌ 데이터에서 '{sport_column}' 컬럼을 찾을 수 없습니다.")
    st.info(f"💡 현재 시스템이 인식한 상위 10개 컬럼 목록:\n{list(df.columns[:10])}")
    st.stop()

selected_sport = st.sidebar.selectbox("🎯 스포츠 종목 선택", sports_list)

# 선택한 종목에 따라 데이터 필터링
if selected_sport == "전체 종목":
    filtered_df = df
else:
    filtered_df = df[df[sport_column] == selected_sport]

# ==============================================================================
# 4. 대시보드 메인 타이틀 화면
# ==============================================================================
st.title("⛑️ 스포츠 안전사고 실태조사 대시보드")
st.markdown(f"**📊 현재 분석 중인 그룹:** `{selected_sport}` | 2024년도 체육인 실태조사 기반")
st.write("---")

# ==============================================================================
# 5. 핵심 지표 계산 및 출력 (KPI Metrics)
# ==============================================================================
injury_exp_col = "스포츠 활동 중 부상 당한 경험"

if injury_exp_col in filtered_df.columns:
    total_respondents = len(filtered_df)
    
    # 원본 데이터의 부상 경험 유무(예: 1 혹은 '있음' 등의 문자열 포함 여부)를 유연하게 판단하여 카운트
    injured_count = len(filtered_df[filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험', na=False)])
    
    if total_respondents > 0:
        injury_rate = (injured_count / total_respondents) * 100
    else:
        injury_rate = 0.0
    
    # 3단 레이아웃 메트릭 카드로 시각화
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📊 총 응답자 수", value=f"{total_respondents:,} 명")
    with col2:
        st.metric(label="🤕 부상 경험자 수", value=f"{injured_count:,} 명")
    with col3:
        st.metric(label="📈 부상 발생률", value=f"{injury_rate:.1f} %")
else:
    st.warning(f"⚠️ 부상 데이터 계산을 위한 '{injury_exp_col}' 컬럼이 부재합니다.")

st.write("")
st.markdown("### 📊 부상 사고 패턴 상세 분석")

# 실제로 부상을 당한 경험이 있는 대상자 데이터만 추출하여 그래프 분석에 사용
if injury_exp_col in filtered_df.columns:
    injury_data = filtered_df[filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험', na=False)]
else:
    injury_data = pd.DataFrame()

# ==============================================================================
# 6. 통계 분석 시각화 (시간대별 / 장소별 차트)
# ==============================================================================
if len(injury_data) == 0:
    st.info("ℹ️ 현재 선택된 조건에 부합하는 부상 경험자 데이터가 없습니다.")
else:
    chart_col1, chart_col2 = st.columns(2)
    
    # --- [좌측 차트: 부상 발생 시간대 분포] ---
    with chart_col1:
        st.subheader("⏰ 부상 발생 시간대 분포")
        
        # 설문조사에 포함된 시간대별 컬럼 리스트 정의
        time_cols = ["새벽 시간대", "아침 시간대", "오전 시간대", "점심 시간대", "오후 시간대", "저녁 시간대", "야간 시간대", "심야 시간대"]
        existing_time_cols = [c for c in time_cols if c in df.columns]
        
        if existing_time_cols:
            # 다중 선택형(Checklist) 구조인 시간대별 유효 응답 수 집계
            time_counts = injury_data[existing_time_cols].notna().sum().reset_index()
            time_counts.columns = ['시간대', '부상 건수']
            
            fig_time = px.bar(
                time_counts, 
                x='시간대', 
                y='부상 건수',
                text='부상 건수',
                color='부상 건수',
                color_continuous_scale='Reds'
            )
            fig_time.update_traces(texttemplate='%{text}건', textposition='outside')
            fig_time.update_layout(xaxis_title="설문 시간대", yaxis_title="누적 부상 신고수")
            st.plotly_chart(fig_time, use_container_width=True)
            
        elif "부상을 당한 시간" in injury_data.columns:
            # 단일 선택형 데이터 구조일 경우 처리
            time_series = injury_data["부상을 당한 시간"].value_counts().reset_index()
            time_series.columns = ['시간대', '부상 건수']
            
            fig_time = px.bar(time_series, x='시간대', y='부상 건수', color='부상 건수', color_continuous_scale='Oranges')
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("💡 시간대별 빈도를 분석할 수 있는 열이 매핑되지 않았습니다.")

    # --- [우측 차트: 부상 발생 장소 순위] ---
    with chart_col2:
        st.subheader("📍 부상 발생 장소 TOP 10")
        
        # 설문에 표기된 정제된 장소 열이름 지정
        place_col = "부상을 당한 장소(또는 시설)"
        if place_col in injury_data.columns:
            place_counts = injury_data[place_col].value_counts().reset_index()
            place_counts.columns = ['장소/시설', '부상 건수']
            
            # 상위 10개 장소를 파이(도넛) 차트로 시각화
            fig_place = px.pie(
                place_counts.head(10), 
                values='부상 건수', 
                names='장소/시설',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.YlOrRd_r
            )
            fig_place.update_traces(textinfo='percent+label', textposition='inside')
            st.plotly_chart(fig_place, use_container_width=True)
        else:
            st.info("💡 '부상을 당한 장소(또는 시설)' 컬럼을 데이터셋에서 찾을 수 없습니다.")

# ==============================================================================
# 7. 하단 영역 - 필터링된 원본 데이터 미리보기 기증
# ==============================================================================
st.write("---")
if st.checkbox("📁 현재 필터링된 원본 데이터 테이블 상세 보기 (상위 50행)"):
    st.dataframe(filtered_df.head(50))
