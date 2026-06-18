import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("🏃‍♂️ 스포츠 안전사고 데이터 시각화 대시보드")
st.markdown("설문조사의 복잡한 코드 대신, 일반인들이 쉽게 이해할 수 있도록 한글 명칭으로 변환하여 보여줍니다.")

@st.cache_data
def load_and_clean_data():
    # 1. 데이터 로드 (첫 두 행이 헤더 형태이므로, 실제 데이터 가공을 위해 수집)
    df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", low_memory=False)
    
    # 가이드에 따른 주요 컬럼 정의
    # Q3_1: 스포츠 종목명, Q10: 부상 시간대, Q11: 부상 장소
    col_sports = 'Q3_1'
    col_time = 'Q10'
    col_place = 'Q11'
    
    # 분석에 필요한 열만 추출하고 결측치 제거
    # 첫 번째 행이나 두 번째 행에 질문지가 섞여 있을 수 있으므로 숫자로 변환 가능한 데이터만 필터링
    df_clean = df[[col_sports, col_time, col_place]].dropna().copy()
    
    # 헤더 행 등이 섞여있을 경우를 대비해 numeric 변환 처리
    df_clean[col_time] = pd.to_numeric(df_clean[col_time], errors='coerce')
    df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')
    df_clean = df_clean.dropna()

    # 2. 일반인들이 알기 쉬운 한글 텍스트로 치환 매핑 (GUIDE.csv 기반)
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
    
    # 실제 데이터 치환
    df_clean['부상시간'] = df_clean[col_time].map(time_map)
    df_clean['부상장소'] = df_clean[col_place].map(place_map)
    df_clean['스포츠종목'] = df_clean[col_sports].astype(str)
    
    # 매핑되지 않은 잔여 결측치 제거
    df_clean = df_clean.dropna(subset=['부상시간', '부상장소'])
    
    return df_clean

try:
    data = load_and_clean_data()

    # ----------------------------------------------------
    # 사이드바 필터링
    # ----------------------------------------------------
    st.sidebar.header("🔍 조건 선택")
    sports_list = ["전체 종목 보기"] + sorted(data['스포츠종목'].unique().tolist())
    selected_sport = st.sidebar.selectbox("비교하고 싶은 스포츠를 선택하세요", sports_list)

    if selected_sport != "전체 종목 보기":
        filtered_df = data[data['스포츠종목'] == selected_sport]
    else:
        filtered_df = data

    # ----------------------------------------------------
    # 리포트 화면 구성
    # ----------------------------------------------------
    
    # 1. 종목별 부상 순위 (전체 보기일 때만 제공)
    if selected_sport == "전체 종목 보기":
        st.subheader("🏆 어떤 종목에서 부상이 가장 많이 발생했을까?")
        top_sports = data['스포츠종목'].value_counts().head(10).reset_index()
        top_sports.columns = ['스포츠 종목', '부상 신고 건수']
        
        fig_sports = px.bar(
            top_sports, 
            x='부상 신고 건수', 
            y='스포츠 종목', 
            orientation='h',
            color='부상 신고 건수',
            color_continuous_scale='Reds',
            text_auto=True
        )
        fig_sports.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_sports, use_container_width=True)
        st.markdown("---")

    # 2. 시간대 및 장소 분석
    st.subheader(f"📊 {selected_sport} 부상 위험 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🕒 **언제 가장 위험할까요?** (부상 시간대)")
        time_counts = filtered_df['부상시간'].value_counts().reset_index()
        time_counts.columns = ['시간대', '부상 건수']
        
        fig_time = px.pie(
            time_counts, 
            values='부상 건수', 
            names='시간대',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_time.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_time, use_container_width=True)
        
    with col2:
        st.markdown("### 📍 **어디서 사고가 많이 날까요?** (부상 장소)")
        place_counts = filtered_df['부상장소'].value_counts().reset_index()
        place_counts.columns = ['장소', '부상 건수']
        
        fig_place = px.bar(
            place_counts, 
            x='부상 건수', 
            y='장소', 
            orientation='h',
            color='부상 건수',
            color_continuous_scale='Blues',
            text_auto=True
        )
        fig_place.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_place, use_container_width=True)

    # 요약 통계 정보 제공
    st.markdown("---")
    st.subheader("💡 데이터 요약 가이드")
    
    total_accidents = len(filtered_df)
    most_frequent_time = filtered_df['부상시간'].mode()[0] if not filtered_df.empty else "데이터 없음"
    most_frequent_place = filtered_df['부상장소'].mode()[0] if not filtered_df.empty else "데이터 없음"
    
    st.info(
        f"**[{selected_sport}]** 분석 결과 총 **{total_accidents:,}건**의 안전사고 데이터가 집계되었습니다.\n\n"
        f"• 가장 부상이 자주 일어나는 시간대는 **{most_frequent_time}** 입니다.\n"
        f"• 가장 주의해야 할 장소는 **{most_frequent_place}** 입니다."
    )

except Exception as e:
    st.error(f"데이터 정제 중 오류가 발생했습니다. 파일 구조를 다시 확인해 주세요. 오류 내용: {e}")
