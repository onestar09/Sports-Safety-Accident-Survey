import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("🏃‍♂️ 스포츠 안전사고 데이터 시각화 대시보드")
st.markdown("데이터의 컬럼 구조를 자동으로 분석하여 일반인들이 알기 쉬운 한글 명칭으로 변환합니다.")

@st.cache_data
def load_and_clean_data():
    # 1. 데이터 로드 (헤더 문제를 방지하기 위해 0번, 1번 행을 모두 고려할 수 있도록 함)
    # 로우 데이터를 읽은 후 실제 컬럼 이름들을 확인합니다.
    df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", low_memory=False)
    
    # [컬럼 자동 찾기 로직] 
    # 에러 방지를 위해 실제 컬럼명 중 해당 키워드가 포함된 첫 번째 컬럼을 자동으로 매핑합니다.
    col_sports = None
    col_time = None
    col_place = None
    
    for col in df.columns:
        col_str = str(col).strip()
        if 'Q3_1' in col_str or '종목' in col_str:
            col_sports = col
        elif 'Q10' in col_str or '시간' in col_str:
            col_time = col
        elif 'Q11' in col_str or '장소' in col_str:
            col_place = col

    # 만약 자동 매핑에 실패했을 경우를 위한 방어 코드 (임의로 2, 3, 4번째 열 지정)
    if not col_sports: col_sports = df.columns[1]
    if not col_time: col_time = df.columns[2]
    if not col_place: col_place = df.columns[3]
    
    # 화면에 실제 매핑된 컬럼 정보를 안내용으로 출력 (디버깅용)
    st.sidebar.info(f"💡 인식된 데이터 컬럼:\n- 종목: {col_sports}\n- 시간: {col_time}\n- 장소: {col_place}")

    # 분석에 필요한 열만 추출하고 결측치 제거
    df_clean = df[[col_sports, col_time, col_place]].copy()
    
    # 첫 행이 한글 설명글 문장(텍스트)일 수 있으므로, 숫자로 변환되지 않는 행은 제외 처리
    df_clean[col_time] = pd.to_numeric(df_clean[col_time], errors='coerce')
    df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')
    df_clean = df_clean.dropna()

    # 2. 일반인들이 알기 쉬운 한글 텍스트로 치환 매핑 (GUIDE 기반)
    time_map = {
        1: "새벽 (06시 미만)",
        2: "오전 (06시 ~ 12시 미만)",
        3: "오후 (12시 ~ 18시 미만)",
        4: "야간 (18시 ~ 24시 미만)",
        5: "심야 (24시 ~ 06시 미만)"
    }
    
    place_map = {
        1: "공공 체육시설 (지자체 운영 등)",
        2: "민간 체육시설 (헬스장, 요가룸 등)",
        3: "학교 체육시설 (초/중/고/대학교)",
        4: "자가 시설 (집, 아파트 내 시설)",
        5: "자연 환경 (산, 바다, 강, 길거리)",
        6: "기타 장소"
    }
    
    # 데이터 치환 적용
    df_clean['부상시간'] = df_clean[col_time].map(time_map)
    df_clean['부상장소'] = df_clean[col_place].map(place_map)
    df_clean['스포츠종목'] = df_clean[col_sports].astype(str)
    
    # 가이드에 없는 값이거나 변환이 안 된 데이터 정제
    df_clean = df_clean.dropna(subset=['부상시간', '부상장소'])
    
    # 혹시 설문안내 텍스트가 종목명에 들어간 경우 필터링
    df_clean = df_clean[~df_clean['스포츠종목'].str.contains('스포츠|종목|Q3', na=False)]
    
    return df_clean

try:
    data = load_and_clean
