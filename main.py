import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(
    page_title="2024 스포츠 안전사고 실태조사 대시보드",
    page_icon="⛑️",
    layout="wide"
)

# 2. 이중 헤더 결합 및 데이터 로드 함수
@st.cache_data
def load_data():
    file_path = "2024_스포츠_안전사고_실태조사_체육인.csv"
    
    # 인코딩 방식 예외 처리하며 읽기 (0, 1번 행을 동시에 헤더로 지정)
    try:
        df = pd.read_csv(file_path, header=[0, 1])
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, header=[0, 1], encoding='cp949')
    
    # 상위 분류(기호명 미지정 포함)와 하위 문항 코드를 결합하여 새로운 단일 컬럼명 생성
    new_columns = []
    for col in df.columns:
        # Unnamed로 시작하는 결측치 텍스트 제거
        top = "" if "Unnamed:" in col[0] else col[0].strip()
        bottom = "" if "Unnamed:" in col[1] else col[1].strip()
        
        if top and bottom:
            full_name = f"{top}_{bottom}"
        elif bottom:
            full_name = bottom
        else:
            full_name = top
            
        # 줄바꿈 및 탭 문자 완전 정제
        full_name = full_name.replace('\n', '').replace('\r', '').replace('\t', '').strip()
        new_columns.append(full_name)
        
    df.columns = new_columns
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ 데이터를 불러오지 못했습니다. 파일명과 위치를 확인하세요. (오류: {e})")
    st.stop()

# ==============================================================================
# 3. 캡처본 기반 고정 컬럼 자동 탐색 및 매핑
# ==============================================================================
sport_column = None
injury_exp_col = None

for col in df.columns:
    # 종목 컬럼 찾기 (SQ2 텍스트가 포함된 열 타겟팅)
    if "SQ2" in col or "참여스포츠" in col:
        sport_column = col
    # 부상 여부 컬럼 찾기 (Q1 텍스트 혹은 부상 경험 문구 타겟팅)
    if "부상 경험" in col or "Q1" in col:
        if "시간" not in col and "장소" not in col:  # 시간/장소 문항 혼선 방지
            injury_exp_col = col

# 만약 매핑에 실패했을 경우를 대비한 최후의 보루
if not sport_column:
    sport_column = [c for c in df.columns if "SQ" in c][0] if any("SQ" in c for c in df.columns) else df.columns[4]
if not injury_exp_col:
    injury_exp_col = [c for c in df.columns if "Q1" in c][0] if any("Q1" in c for c in df.columns) else df.columns[10]

# ==============================================================================
# 4. 사이드바 종목 필터링
# ==============================================================================
st.sidebar.title("🔍 대시보드 필터")
st.sidebar.markdown("원하는 스포츠 종목을 선택하세요.")

# 종목 리스트 생성
sports_list = ["전체 종목"] + sorted(df[sport_column].dropna().astype(str).unique().tolist())
# 이상 데이터(컬럼명 중복 유입 등) 제외
sports_list = [s for s in sports_list if s and "SQ" not in s]

selected_sport = st.sidebar.selectbox("🎯 스포츠 종목 선택", sports_list)

if selected_sport == "전체 종목":
    filtered_df = df
else:
    filtered_df = df[df[sport_column].astype(str) == selected_sport]

# ==============================================================================
# 5. 메인 대시보드 UI 영역
# ==============================================================================
st.title("⛑️ 스포츠 안전사고 실태조사 대시보드")
st.markdown(f"**📊 현재 분석 대상:** `{selected_sport}`")
st.write("---")

# KPI 지표 (부상률)
total_res = len(filtered_df)
# 데이터셋 내 '1' 또는 '있음', '경험'이 포함된 부상 유효 샘플 집계
injured_res = len(filtered_df[filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험', na=False)])
rate = (injured_res / total_res * 100) if total_res > 0 else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("📊 총 응답자 수", f"{total_res:,} 명")
c2.metric("🤕 부상 경험자 수", f"{injured_res:,} 명")
c3.metric("📈 부상률", f"{rate:.1f} %")

st.write("")
st.markdown("### 📊 부상 사고 패턴 상세 시각화")

# 부상자 응답 데이터만 슬라이싱
injury_data = filtered_df[filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험', na=False)]

if len(injury_data) == 0:
    st.info("ℹ️ 현재 선택된 종목 그룹에는 부상 데이터가 존재하지 않습니다.")
else:
    ch1, ch2 = st.columns(2)
    
    # --- [좌측: 부상 시간대 분석] ---
    with ch1:
        st.subheader("⏰ 부상 발생 시간대 분포")
        # 컬럼 이름에 '시간'이라는 단어가 들어간 열을 모두 취합
        time_cols = [c for c in df.columns if "시간" in c]
        
        if len(time_cols) > 1:
            # 다중 선택 체크박스 문항일 때 처리
            time_counts = injury_data[time_cols].notna().sum().reset_index()
            time_counts.columns = ['시간대', '부상 건수']
            # 가독성을 위해 문항 코드가 결합된 이름 정제
            time_counts['시간대'] = time_counts['시간대'].apply(lambda x: x.split('_')[-1])
            
            fig_time = px.bar(time_counts, x='시간대', y='부상 건수', text='부상 건수', color='부상 건수', color_continuous_scale='Reds')
            fig_time.update_traces(texttemplate='%{text}건', textposition='outside')
            st.plotly_chart(fig_time, use_container_width=True)
        elif len(time_cols) == 1:
            # 단일 선택형 라디오 문항일 때 처리
            t_counts = injury_data[time_cols[0]].value_counts().reset_index()
            t_counts.columns = ['시간대', '부상 건수']
            fig_time = px.bar(t_counts, x='시간대', y='부상 건수', color='부상 건수', color_continuous_scale
    
