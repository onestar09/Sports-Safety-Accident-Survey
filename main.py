import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 레이아웃 기본 설정
st.set_page_config(
    page_title="2024 스포츠 안전사고 실태조사 대시보드",
    page_icon="⛑️",
    layout="wide"
)

# 2. 데이터 로드 함수 (헤더 구조 최적화)
@st.cache_data
def load_data():
    file_path = "2024_스포츠_안전사고_실태조사_체육인.csv"
    try:
        # 데이터의 실제 문항이 있는 header=1로 로드합니다.
        df = pd.read_csv(file_path, header=1)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, header=1, encoding='cp949')
    
    # 컬럼명에 포함된 줄바꿈(\n), 탭(\t), 앞뒤 공백을 완벽하게 제거하여 정제합니다.
    df.columns = df.columns.str.replace(r'[\r\n\t]+', '', regex=True).str.strip()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ 데이터를 로드하지 못했습니다. 파일명과 위치를 확인해 주세요. (오류: {e})")
    st.stop()

# ==============================================================================
# 3. [핵심] 컬럼명 자동 탐색 알고리즘 (글자 매핑 에러 원천 차단)
# ==============================================================================
sport_column = None
injury_exp_col = None

for col in df.columns:
    # '참여'와 '종목'이라는 글자가 어떤 형태로든 포함되어 있으면 종목 컬럼으로 지정
    if "참여" in col and "종목" in col:
        sport_column = col
    # '부상'과 '경험'이라는 글자가 포함되어 있으면 부상 경험 컬럼으로 지정
    if "부상" in col and "경험" in col:
        injury_exp_col = col

# 만약 위 조건으로도 찾지 못했을 때를 대비한 비상용 가드 코드
if not sport_column:
    # 캡처화면에 보였던 '참여스포츠및 종목' 혹은 4번째 위치한 컬럼 강제 지정
    sport_column = "참여스포츠및 종목" if "참여스포츠및 종목" in df.columns else df.columns[3]
if not injury_exp_col:
    injury_exp_col = "스포츠 활동 중 부상 경험" if "스포츠 활동 중 부상 경험" in df.columns else df.columns[10]

# ==============================================================================
# 4. 사이드바 필터링 영역
# ==============================================================================
st.sidebar.title("🔍 대시보드 필터")
st.sidebar.markdown("원하는 스포츠 종목을 선택하세요.")

if sport_column in df.columns:
    # 빈 값 제거 후 고유 종목 리스트 생성
    sports_list = ["전체 종목"] + sorted(df[sport_column].dropna().astype(str).unique().tolist())
else:
    st.error(f"❌ 시스템이 종목 컬럼을 자동으로 특정하지 못했습니다.")
    st.info(f"💡 현재 인식된 상위 컬럼 목록: {list(df.columns[:10])}")
    st.stop()

selected_sport = st.sidebar.selectbox("🎯 스포츠 종목 선택", sports_list)

# 선택한 종목에 따른 필터링
if selected_sport == "전체 종목":
    filtered_df = df
else:
    filtered_df = df[df[sport_column].astype(str) == selected_sport]

# ==============================================================================
# 5. 메인 대시보드 UI 및 통계 지표 (KPI)
# ==============================================================================
st.title("⛑️ 스포츠 안전사고 실태조사 대시보드")
st.markdown(f"**📊 현재 분석 대상 종목:** `{selected_sport}`")
st.write("---")

# 핵심 지표 계산
total_res = len(filtered_df)

# 부상 경험이 '있다' 혹은 '1', '경험이 있다'인 경우를 유연하게 카운트
if injury_exp_col in filtered_df.columns:
    injury_condition = filtered_df[injury_exp_col].astype(str).str.contains('1|있음|경험|유|예', na=False)
    injured_res = len(filtered_df[injury_condition])
    rate = (injured_res / total_res * 100) if total_res > 0 else 0.0
else:
    injured_res = 0
    rate = 0.0

col1, col2, col3 = st.columns(3)
col1.metric(label="📊 총 응답자 수", value=f"{total_res:,} 명")
col2.metric(label="🤕 부상 경험자 수", value=f"{injured_res:,} 명")
col3.metric(label="📈 부상률", value=f"{rate:.1f} %")

st.write("")
st.markdown("### 📊 부상 사고 패턴 상세 시각화")

# 실제로 부상 경험이 있는 데이터만 필터링하여 그래프 생성
if injury_exp_col in filtered_df.columns:
    injury_data = filtered_df[injury_condition]
else:
    injury_data = pd.DataFrame()

if len(injury_data) == 0:
    st.info("ℹ️ 현재 선택된 종목 그룹에는 부상 데이터 통계가 존재하지 않습니다.")
else:
    chart_col1, chart_col2 = st.columns(2)
    
    # --- [좌측 차트: 부상이 잦은 시간대 분석] ---
    with chart_col1:
        st.subheader("⏰ 부상 발생 시간대 분포")
        
        # '시간' 단어가 포함된 컬럼들을 찾아 빈도 분석
        time_cols = [c for c in df.columns if "시간" in c]
        
        if time_cols:
            # 부상 데이터와 가장 밀접한 뒤쪽 컬럼 혹은 대표 시간대 컬럼 선택
            target_time_col = time_cols[-1]
            
            t_counts = injury_data[target_time_col].value_counts().reset_index()
            t_counts.columns = ['시간대', '부상 건수']
            
            # 숫자 코드로 되어 있을 경우를 대비한 가독성 변환 매핑
            time_map = {'1': '새벽', '2': '오전', '3': '오후', '4': '야간', 1: '새벽', 2: '오전', 3: '오후', 4: '야간'}
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
            st.info("💡 데이터 내에서 시간대 관련 컬럼을 식별하지 못했습니다.")

    # --- [우측 차트: 부상이 자주 발생하는 장소 분석] ---
    with chart_col2:
        st.subheader("📍 부상 발생 장소 TOP 10")
        
        # '장소' 또는 '시설' 단어가 포함된 컬럼 찾기
        place_cols = [c for c in df.columns if "장소" in c or "시설" in c]
        
        if place_cols:
            target_place = place_cols[0]
            p_counts = injury_data[target_place].value_counts().reset_index()
            p_counts.columns = ['장소/시설', '부상 건수']
            
            # 숫자 코드로 되어 있을 경우를 대비한 가독성 변환 매핑
            place_map = {'1': '공공 체육시설', '2': '민간 체육시설', '3': '학교 체육시설', '4': '기타 환경', 1: '공공 체육시설', 2: '민간 체육시설', 3: '학교 체육시설', 4: '기타 환경'}
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
            st.info("💡 데이터 내에서 장소/시설 관련 컬럼을 식별하지 못했습니다.")

# 6. 하단 데이터 원본 확인 기능
st.write("---")
if st.checkbox("📁 데이터 정상 맵핑 진단 로그 및 원본 보기"):
    st.write(f"⚙️ **시스템 매핑 완료된 종목 열 이름:** `{sport_column}`")
    st.write(f"⚙️ **시스템 매핑 완료된 부상 경험 열 이름:** `{injury_exp_col}`")
    st.dataframe(filtered_df.head(50))
