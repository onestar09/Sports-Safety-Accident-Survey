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
        
        # 첫 번째 행과 두 번째 행을 결합하여 고유한 단일 헤더 생성
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
        col_time = None
        col_place = None
        
        for col in df.columns:
            # 주 종목 컬럼 찾기 (SQ2#1 등으로 시작하거나 참여스포츠/종목 키워드 포함)
            if ("SQ2" in col or "종목" in col) and ("참여" in col or "주요" in col or "SQ2" in col):
                col_sports = col
                break  # 대표 종목 하나를 타겟팅
        
        for col in df.columns:
            if "부상" in col and "시간" in col:
                col_time = col
            elif "부상" in col and "장소" in col:
                col_place = col

        # 만약 자동 검색에 실패했을 경우를 대비한 완전 무결 방어 코드 (위치 기준)
        if not col_sports:
            col_sports = [c for c in df.columns if "SQ2" in c or "종목" in c][0] if [c for c in df.columns if "SQ2" in c or "종목" in c] else df.columns[3]
        if not col_time:
            col_time = [c for c in df.columns if "시간" in c][0] if [c for c in df.columns if "시간" in c] else df.columns[4]
        if not col_place:
            col_place = [c for c in df.columns if "장소" in c][0] if [c for c in df.columns if "장소" in c] else df.columns[5]

        # 3. 필요한 데이터 추출 및 숫자형 변환
        df_clean = df[[col_sports, col_time, col_place]].copy()
        df_clean[col_sports] = pd.to_numeric(df_clean[col_sports], errors='coerce')
        df_clean[col_time] = pd.to_numeric(df_clean[col_time], errors='coerce')
        df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')
        df_clean = df_clean.dropna()

        # 4. [GUIDE 참고] 숫자 코드를 실제 한글 종목 이름으로 바꾸는 딕셔너리
        sports_map = {
            1: "가라테", 2: "검도", 3: "게이트볼", 4: "골프(스크린골프 포함)", 5: "국학기공",
            6: "궁도", 7: "그라운드골프", 8: "근대5종", 9: "농구", 10: "당구(포켓볼 포함)",
            11: "댄스스포츠", 12: "럭비", 13: "레슬링", 14: "롤러(인라인스케이트/하키 등)", 15: "루지",
            16: "바둑", 17: "바이애슬론", 18: "배구", 19: "배드민턴", 20: "보디빌딩(헬스)",
            21: "복싱(권투)", 22: "볼링", 23: "봅슬레이/스켈레톤", 24: "빙상(스케이트/피겨 등)", 25: "사격",
            26: "산악(등산, 클라이밍 등)", 27: "세팍타크로", 28: "소프트테니스(정구)", 29: "수상스키/웨이크보드", 30: "수영(수중발레, 다이빙, 수구 등)",
            31: "스쿼시", 32: "스키/스노우보드", 33: "승마", 34: "씨름", 35: "아이스하키",
            36: "야구/소프트볼", 37: "양궁", 38: "에어로빅", 39: "역도", 40: "요트",
            41: "우슈", 42: "유도", 43: "육상(단거리, 중거리, 마라톤, 조깅 등)", 44: "자전거(사이클, MTB 등
