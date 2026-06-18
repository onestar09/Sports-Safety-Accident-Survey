import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("📊 스포츠 안전사고 데이터 시각화 대시보드")
st.markdown("설문지의 숫자 코드를 일반인들이 알기 쉬운 종목 명칭과 항목들로 자동 변환하여 보여줍니다.")

@st.cache_data
def load_and_clean_data():
    try:
        # 1. 원본 데이터 로드 (헤더 병합 처리)
        df_raw = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=None, low_memory=False)
        
        header_row1 = df_raw.iloc[0].fillna("").astype(str)
        header_row2 = df_raw.iloc[1].fillna("").astype(str)
        
        combined_headers = []
        for h1, h2 in zip(header_row1, header_row2):
            full_header = (h1 + "_" + h2).strip("_").replace("\n", "").replace(" ", "")
            combined_headers.append(full_header)
            
        df_raw.columns = combined_headers
        df = df_raw.iloc[2:].reset_index(drop=True)
        
        # 2. 타겟 컬럼 검색
        col_sports = None
        col_place = None
        
        for col in df.columns:
            if ("SQ2" in col or "종목" in col) and ("참여" in col or "주요" in col or "SQ2" in col):
                col_sports = col
                break
        
        for col in df.columns:
            if "부상" in col and "장소" in col:
                col_place = col
                break

        if not col_sports:
            col_sports = [c for c in df.columns if "SQ2" in c or "종목" in c][0] if [c for c in df.columns if "SQ2" in c or "종목" in c] else df.columns[3]
        if not col_place:
            col_place = [c for c in df.columns if "장소" in c][0] if [c for c in df.columns if "장소" in c] else df.columns[5]

        # 3. [시간대 다중 응답 설정] - 597~604번째 열
        time_cols_indices = range(597, 605)
        time_cols = [df_raw.columns[i] for i in time_cols_indices]
        time_labels = [str(df_raw.iloc[1, i]).strip() for i in time_cols_indices]
