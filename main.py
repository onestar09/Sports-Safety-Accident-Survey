import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="2024 스포츠 안전사고 실태조사 대시보드",
    page_icon="⛑️",
    layout="wide"
)

# 2. 데이터 로드 및 인코딩 해결
@st.cache_data
def load_data():
    # 파일 구조에 맞게 헤더를 자동으로 정제하며 읽기
    try:
        df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=1)
    except UnicodeDecodeError:
        df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=1, encoding='cp949')
    
    # 컬럼명 내의 줄바꿈 및 공백 완전 제거
    df.columns = df.columns.str.replace(r'[\r\n\t]+', '', regex=True).str.strip()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ 데이터를 읽어오지 못했습니다. 파일명을 확인해주세요. (오류: {e})")
    st.stop()

# ==============================================================================
# [핵심] 컬럼명 자동 매핑 알고리즘 (문항 코드로 되어 있는 경우 구출용)
# ==============================================================================
sport_column = None
injury_exp_col = None
place_col = None

for col in df.columns:
    # 1. 종목 컬럼 찾기 ('참여스포츠', '종목', 'SQ2' 등 매핑)
    if any(k in col for k in ["참여스포츠", "종목", "스포츠종목"]):
        sport_column = col
    # 2. 부상 경험 컬럼 찾기 ('부상 당한 경험', '부상경험', 'Q1_')
    if any(k in col for k in ["부상 당한 경험", "부상 경험", "부상여부"]):
        injury_exp_col = col
    # 3. 장소 컬럼 찾기 ('장소', '시설')
    if any(k in col for k in ["장소", "시설"]):
        place_col = col

# 만약 자동 탐지에 실패했을 때를 대비한 하드코딩 백업 (캡처 화면 기반 비상 대책)
if not sport_column:
    # 캡처에 보이는 SQ2를 비상용 종목 컬럼으로 설정해봅니다.
    sport_column = "SQ2" if "SQ2" in df.columns else df.columns[4] 
if not injury_exp_col:
    injury_exp_col = "Q1" if "Q1" in df.columns else df.columns[10]
if not place_col:
    place_col = "Q3" if "Q3" in df.columns else df.columns[15]

# ==============================================================================
# 3. 사이드바 필터링
# ==============================================================================
st.sidebar.title("🔍 대시보드 필터")

# 선택 가능한 종목 리스트 생성
if sport_column in df.columns:
    sports_list = ["전체 종목"] + sorted(df[sport_column].dropna().astype(str).unique().tolist())
else:
    sports_list = ["전체 종목"]

selected_sport = st.sidebar.selectbox("🎯 스포츠 종목 선택", sports_list)

# 데이터 필터링
if selected_sport == "전체 종목":
    filtered_df = df
else:
    filtered_df = df[df[sport_column].astype(str) == selected_sport]

# 4. 메인 화면 타이틀
st.title("⛑️ 스포츠 안전사고 실태조사 대시보드")
st.markdown(f"**현재 분석 종목:** `{selected_sport}`")
st.write("---")

# 5. 메트릭스 (부상률 계산)
if injury_exp_col in filtered_df.columns:
    total_res = len(filtered_df)
    # 1번 혹은 '있음'을 선택한 경우를 유연하게 카운트
    injured_res = len(filtered_df[filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험', na=False)])
    rate = (injured_res / total_res * 100) if total_res > 0 else 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📊 총 응답자 수", f"{total_res:,} 명")
    c2.metric("🤕 부상 경험자 수", f"{injured_res:,} 명")
    c3.metric("📈 부상률", f"{rate:.1f} %")
else:
    st.warning("부상 여부를 판단할 컬럼을 데이터에서 찾지 못했습니다.")

st.write("")
st.markdown("### 📊 상세 통계 그래프 분석")

# 부상자 데이터만 추출
if injury_exp_col in filtered_df.columns:
    injury_data = filtered_df[filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험', na=False)]
else:
    injury_data = pd.DataFrame()

if len(injury_data) == 0:
    st.info("선택한 그룹에 부상 데이터가 존재하지 않습니다.")
else:
    ch1, ch2 = st.columns(2)
    
    # --- [좌측: 시간대 분석] ---
    with ch1:
        st.subheader("⏰ 부상 발생 시간대 분포")
        # 데이터셋에 '시간대' 단어가 들어간 컬럼들을 묶어서 집계 시도
        time_cols = [c for c in df.columns if "시간대" in c or "시간" in c]
        
        if time_cols and len(time_cols) > 1:
            time_counts = injury_data[time_cols].notna().sum().reset_index()
            time_counts.columns = ['시간대', '부상 건수']
            fig_time = px.bar(time_counts, x='시간대', y='부상 건수', text='부상 건수', color='부상 건수', color_continuous_scale='Reds')
            fig_time.update_traces(texttemplate='%{text}건', textposition='outside')
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            # 시간대 컬럼이 딱 하나로 뭉쳐져 있을 때 (예: Q4 등)
            target_time_col = time_cols[0] if time_cols else None
            if target_time_col:
                t_counts = injury_data[target_time_col].value_counts().reset_index()
                t_counts.columns = ['시간대', '부상 건수']
                fig_time = px.bar(t_counts, x='시간대', y='부상 건수', color='부상 건수', color_continuous_scale='Oranges')
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.info("데이터 내에서 시간대 관련 컬럼을 식별할 수 없습니다.")

    # --- [우측: 장소 분석] ---
    with ch2:
        st.subheader("📍 부상 발생 장소 순위")
        if place_col in injury_data.columns:
            p_counts = injury_data[place_col].value_counts().reset_index()
            p_counts.columns = ['장소/시설', '부상 건수']
            fig_place = px.pie(p_counts.head(10), values='부상 건수', names='장소/시설', hole=0.
