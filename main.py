import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="2024 스포츠 안전사고 실태조사 대시보드",
    page_icon="⛑️",
    layout="wide"
)

# 2. 데이터 로드 함수 (캐싱 처리로 속도 최적화)
@st.cache_data
def load_data():
    # 데이터 불러오기 (첫 2개 행이 다중 헤더 구조이므로 2번째 행을 기준으로 읽거나 적절히 처리)
    # 한글 깨짐 방지를 위해 cp949 또는 utf-8-sig 사용
    try:
        df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=1)
    except UnicodeDecodeError:
        df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=1, encoding='cp949')
    
    # 컬럼명 공백 제거
    df.columns = df.columns.str.strip()
    return df

# 데이터 로드 안내
try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 읽어오는 중 오류가 발생했습니다. 파일명을 확인해주세요. 오류 메시지: {e}")
    st.stop()

# 3. 사이드바 - 대시보드 컨트롤 및 필터
st.sidebar.title("🔍 대시보드 필터")
st.sidebar.markdown("분석하고 싶은 종목을 선택하세요.")

# 종목 리스트 추출 (결측치 제거)
sport_column = "참여스포츠 및 종목"
if sport_column in df.columns:
    sports_list = ["전체 종목"] + sorted(df[sport_column].dropna().unique().tolist())
else:
    st.error(f"'{sport_column}' 컬럼을 찾을 수 없습니다. 데이터 컬럼을 확인해주세요.")
    st.stop()

selected_sport = st.sidebar.selectbox("🎯 스포츠 종목 선택", sports_list)

# 데이터 필터링 규칙
if selected_sport == "전체 종목":
    filtered_df = df
else:
    filtered_df = df[df[sport_column] == selected_sport]

# 4. 메인 화면 타이틀
st.title("⛑️ 스포츠 안전사고 실태조사 대시보드 (체육인)")
st.markdown(f"**현재 선택된 종목:** `{selected_sport}` | 데이터 기반 안전사고 패턴 분석 웹앱")
st.hr()

# 5. 핵심 지표 (Metrics) - 종목별 부상률 계산
# '스포츠 활동 중 부상 당한 경험' 컬럼 분석 (예시: 1=경험 있음, 2=없음)
injury_exp_col = "스포츠 활동 중 부상 당한 경험"

if injury_exp_col in filtered_df.columns:
    total_respondents = len(filtered_df)
    # 데이터 값 유형에 따라 유연하게 카운트 (문자열 '1', 숫자 1, 혹은 '있음' 등 대응)
    injured_count = len(filtered_df[filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험', na=False)])
    
    if total_respondents > 0:
        injury_rate = (injured_count / total_respondents) * 100
    else:
        injury_rate = 0.0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📊 총 응답자 수", value=f"{total_respondents:,} 명")
    with col2:
        st.metric(label="🤕 부상 경험자 수", value=f"{injured_count:,} 명")
    with col3:
        st.metric(label="📈 해당 그룹 부상률", value=f"{injury_rate:.1f} %")
else:
    st.warning("부상률 계산을 위한 '스포츠 활동 중 부상 당한 경험' 컬럼을 매핑할 수 없습니다.")

st.markdown("### 📊 상세 통계 분석 그래프")

# 부상 경험이 있는 데이터만 대상으로 시간대/장소 분석 진행
injury_data = filtered_df[filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험', na=False)]

if len(injury_data) == 0:
    st.info("선택한 조건에 해당하는 부상 경험자 데이터가 없습니다.")
else:
    # 레이아웃 나누기 (왼쪽: 시간대, 오른쪽: 장소)
    chart_col1, chart_col2 = st.columns(2)
    
    # --- [좌측: 부상이 잦은 시간대 분석] ---
    with chart_col1:
        st.subheader("⏰ 부상 발생 시간대 분포")
        
        # 방법 A: '새벽 시간대', '아침 시간대' 등 다중 컬럼이 존재할 경우 취합
        time_cols = ["새벽 시간대", "아침 시간대", "오전 시간대", "점심 시간대", "오후 시간대", "저녁 시간대", "야간 시간대", "심야 시간대"]
        existing_time_cols = [c for c in time_cols if c in df.columns]
        
        if existing_time_cols:
            # 각 시간대별 체크된 빈도 계산 (보통 값이 들어가 있으면 선택된 것)
            time_counts = injury_data[existing_time_cols].notna().sum().reset_index()
            time_counts.columns = ['시간대', '부상 횟수']
            
            fig_time = px.bar(
                time_counts, 
                x='시간대', 
                y='부상 횟수',
                text='부상 횟수',
                color='부상 횟수',
                color_continuous_scale='Reds',
                labels={'부상 횟수': '신고 건수'}
            )
            fig_time.update_traces(texttemplate='%{text}건', textposition='outside')
            st.plotly_chart(fig_time, use_container_width=True)
            
        # 방법 B: 단일 '부상을 당한 시간' 컬럼이 존재할 경우 가동
        elif "부상을 당한 시간" in injury_data.columns:
            time_series = injury_data["부상을 당한 시간"].value_counts().reset_index()
            time_series.columns = ['시간대', '부상 횟수']
            
            fig_time = px.bar(
                time_series, x='시간대', y='부상 횟수',
                color='부상 횟수', color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("시간대 분석용 컬럼을 매핑할 수 없습니다.")

    # --- [우측: 부상이 자주 일어나는 장소 분석] ---
    with chart_col2:
        st.subheader("📍 부상 발생 장소 순위")
        
        place_col = "부상을 당한 장소(또는 시설)"
        if place_col in injury_data.columns:
            place_counts = injury_data[place_col].value_counts().reset_index()
            place_counts.columns = ['장소/시설', '부상 횟수']
            
            # 데이터가 너무 많을 수 있으므로 상위 10개 장소만 시각화
            place_counts_top10 = place_counts.head(10)
            
            fig_place = px.pie(
                place_counts_top10, 
                values='부상 횟수', 
                names='장소/시설',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu_r
            )
            fig_place.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_place, use_container_width=True)
        else:
            st.info("'부상을 당한 장소(또는 시설)' 컬럼을 찾을 수 없습니다.")

# 6. 하단 데이터 요약 보기
st.hr()
if st.checkbox("📁 필터링된 원본 데이터 일부 보기"):
    st.dataframe(filtered_df.head(50))
