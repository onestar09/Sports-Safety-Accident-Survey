import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 폰트 설정 (Streamlit Cloud 환경용 무난한 폰트 또는 Plotly 중심 활용 추천)
plt.rc('font', family='NanumGothic') 

st.set_page_config(page_title="스포츠 안전사고 통계 대시보드", layout="wide")

st.title("📊 스포츠 안전사고 실태조사 분석 대시보드")
st.markdown("2024년 체육인 대상 스포츠 안전사고 데이터를 바탕으로 종목별, 시간대별, 장소별 부상 현황을 보여줍니다.")

# 1. 데이터 로드
@st.cache_data
def load_data():
    # 데이터 헤더가 여러 줄이거나 특이할 경우를 위해 header=[0,1] 등을 고려해야 할 수 있습니다.
    # 여기서는 일반적인 읽기 후 컬럼 매핑 방식을 취합니다.
    df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", low_memory=False)
    return df

try:
    df = load_data()
    
    # ----------------------------------------------------
    # [중요] 실제 CSV 파일의 컬럼명에 맞게 아래 항목을 수정하세요!
    # ----------------------------------------------------
    # 예시: df.columns에서 '종목', '시간', '장소'를 뜻하는 컬럼명을 찾아 대입해야 합니다.
    col_sports = '스포츠 종목 컬럼명'     # 예: 'Q1_종목' 또는 '스포츠종목'
    col_time = '부상 시간 컬럼명'         # 예: 'Q5_부상시간' 또는 '부상시간대'
    col_place = '부상 장소 컬럼명'        # 예: 'Q6_부상장소' 또는 '부상발생장소'
    
    # 임시 테스트용 가이드 (만약 위 컬럼이 데이터에 없을 때 에러 방지용 안내)
    available_cols = list(df.columns)
    
    if col_sports not in available_cols or col_time not in available_cols or col_place not in available_cols:
        st.warning("⚠️ 현재 코드에 설정된 컬럼명이 데이터셋과 일치하지 않습니다. 아래 실제 컬럼 목록을 보고 코드 상단의 변수명을 수정해 주세요.")
        with st.expander("실제 데이터 컬럼명 확인하기 (클릭)"):
            st.write(available_cols[:30]) # 상위 30개만 출력
        
        # 임시로 첫 3개 컬럼을 할당해 에러를 방지합니다 (시각화는 깨질 수 있음)
        col_sports = available_cols[1] if len(available_cols) > 1 else available_cols[0]
        col_time = available_cols[2] if len(available_cols) > 2 else available_cols[0]
        col_place = available_cols[3] if len(available_cols) > 3 else available_cols[0]

    # 결측치 제거 및 데이터 정제
    df_clean = df[[col_sports, col_time, col_place]].dropna()

    # ----------------------------------------------------
    # 사이드바 필터
    # ----------------------------------------------------
    st.sidebar.header("🔍 데이터 필터링")
    sports_list = ["전체"] + sorted(df_clean[col_sports].unique().tolist())
    selected_sport = st.sidebar.selectbox("분석할 스포츠 종목 선택", sports_list)

    if selected_sport != "전체":
        filtered_df = df_clean[df_clean[col_sports] == selected_sport]
    else:
        filtered_df = df_clean

    # ----------------------------------------------------
    # 메인 대시보드 레이아웃
    # ----------------------------------------------------
    
    # 레이아웃 1: 종목별 부상 비율 (전체 보기일 때 유용)
    if selected_sport == "전체":
        st.subheader("🏆 1. 종목별 부상 발생 빈도 Top 10")
        sports_counts = df_clean[col_sports].value_counts().head(10).reset_index()
        sports_counts.columns = ['종목', '부상 건수']
        
        fig1 = px.bar(sports_counts, x='부상 건수', y='종목', orientation='h',
                      title="가장 부상이 잦은 스포츠 종목 Top 10",
                      color='부상 건수', color_continuous_scale='Reds')
        fig1.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("---")

    # 레이아웃 2: 시간대별 & 장소별 분석 (2단 컬럼 배치)
    st.subheader(f"⏱️ [{selected_sport}] 부상 취약 시간대 및 장소 분석")
    col1, col2 = st.columns(2)

    with col1:
        st.write("### 🕒 어느 시간대에 부상이 잦을까?")
        time_counts = filtered_df[col_time].value_counts().reset_index()
        time_counts.columns = ['시간대', '부상 건수']
        
        # Plotly 파이차트로 시각화
        fig_time = px.pie(time_counts, values='부상 건수', names='시간대', 
                          title=f"{selected_sport} 시간대별 부상 비율",
                          hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_time, use_container_width=True)

    with col2:
        st.write("### 📍 어느 장소에서 부상이 자주 일어날까?")
        place_counts = filtered_df[col_place].value_counts().head(10).reset_index()
        place_counts.columns = ['장소', '부상 건수']
        
        # Plotly 세로 바차트로 시각화
        fig_place = px.bar(place_counts, x='장소', y='부상 건수',
                           title=f"{selected_sport} 주요 부상 발생 장소",
                           color='부상 건수', color_continuous_scale='Viridis')
        st.plotly_chart(fig_place, use_container_width=True)

    # 데이터 원본 보기
    st.markdown("---")
    st.subheader("📋 필터링된 데이터 상세 보기")
    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"데이터를 읽거나 처리하는 중 오류가 발생했습니다: {e}")
