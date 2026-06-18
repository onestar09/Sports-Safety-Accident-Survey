import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("📊 스포츠 안전사고 분석 리포트")
st.markdown("전체 스포츠 종목을 통틀어 어떤 안전사고 부상이 가장 빈번하게 발생하는지 분석합니다.")

@st.cache_data
def load_and_clean_data():
    try:
        # 파일명이 .csv 인지 .csv.csv 인지 자동으로 체크하여 존재하는 파일을 로드합니다.
        file_name = "2024_스포츠_안전사고_실태조사_체육인.csv"
        if not os.path.exists(file_name):
            file_name = "2024_스포츠_안전사고_실태조사_체육인.csv.csv"
            
        # 1. 원본 데이터 로드 (헤더 병합 처리)
        df_raw = pd.read_csv(file_name, header=None, low_memory=False)
        
        header_row1 = df_raw.iloc[0].fillna("").astype(str)
        header_row2 = df_raw.iloc[1].fillna("").astype(str)
        
        combined_headers = []
        for h1, h2 in zip(header_row1, header_row2):
            full_header = (h1 + "_" + h2).strip("_").replace("\n", "").replace(" ", "")
            combined_headers.append(full_header)
            
        df_raw.columns = combined_headers
        df = df_raw.iloc[2:].reset_index(drop=True)
        
        # 2. 부상 부위/종류 관련 컬럼 검색
        col_injury = None
        for col in df.columns:
            if "부상" in col and ("부위" in col or "종류" in col or "증상" in col):
                col_injury = col
                break

        if not col_injury:
            injury_candidates = [c for c in df.columns if "부상" in c and ("부위" in c or "종류" in c or "증상" in c)]
            col_injury = injury_candidates[0] if injury_candidates else df.columns[6]

        # 3. 필요한 데이터 추출 및 숫자형 변환
        df_clean = df[[col_injury]].copy()
        df_clean[col_injury] = pd.to_numeric(df_clean[col_injury], errors='coerce')
        df_clean = df_clean.dropna()

        # 4. 설문지 기준 대표적인 부상 증상/종류 매핑
        injury_map = {
            1: "통증/근육통", 2: "염좌 (삐임/접지름)", 3: "좌상/타박상 (멍)",
            4: "찰과상 (긁힘/까짐)", 5: "열상 (찢어짐/상처)", 6: "골절 (뼈 부러짐)",
            7: "탈구 (관절 빠짐)", 8: "뇌진탕/어지러움", 9: "기타 부상"
        }
        
        df_clean['부상종류'] = df_clean[col_injury].map(injury_map)
        df_clean = df_clean.dropna(subset=['부상종류'])
        
        return df_clean
        
    except Exception as e:
        st.error(f"데이터 정제 중 기술적 오류 발생: {e}")
        return pd.DataFrame()

# 데이터 로드
data = load_and_clean_data()

if not data.empty:
    # 👥 사이드바에 깔끔하게 개발 팀 정보만 노출
    st.sidebar.markdown("### 👥 개발 팀 정보")
    st.sidebar.caption("👨‍💻 **유성우** (Data Engineer)")
    st.sidebar.caption("🎨 **최한별** (UI/UX Engineer)")
    st.sidebar.caption("📊 **박건** (Data Visualization)")

    # 📈 오직 전체 부상 종류 통계 그래프 "만" 화면에 배치
    st.subheader("🤕 대한민국 스포츠 안전사고 주요 부상 유형 통계 (전체 종목 통합)")
    
    injury_counts = data['부상종류'].value_counts().reset_index()
    injury_counts.columns = ['부상 종류', '발생 건수']
    
    fig_injury = px.bar(
        injury_counts, x='발생 건수', y='부상 종류', orientation='h',
        color='발생 건수', color_continuous_scale='Oranges', text_auto=True
    )
    fig_injury.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="부상 발생 건수",
        yaxis_title="부상 종류",
        height=550
    )
    st.plotly_chart(fig_injury, use_container_width=True)
    
    # 하단 크레딧 (푸터)
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.85rem;'>© 2024 스포츠 안전사고 실태조사 분석 대시보드 | Developed by <b>유성우, 최한별, 박건</b></p>", unsafe_allow_html=True)
else:
    st.error("⚠️ 데이터를 불러오지 못했습니다. GitHub 저장소에 CSV 파일이 실제로 업로드되어 있는지 확인해 주세요.")
