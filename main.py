import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("🏃‍♂️ 스포츠 안전사고 데이터 시각화 대시보드")
st.markdown("설문조사 데이터를 분석하여 일반인들도 한눈에 보기 쉽게 시각화합니다.")

@st.cache_data
def load_and_clean_data():
    try:
        # 1. 원본 데이터 로드 (헤더가 복잡하므로 우선 문자열 형태로 통째로 읽어옴)
        df_raw = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=None, low_memory=False)
        
        # 첫 번째 행과 두 번째 행을 결합하여 고유한 단일 헤더 생성
        header_row1 = df_raw.iloc[0].fillna("").astype(str)
        header_row2 = df_raw.iloc[1].fillna("").astype(str)
        
        combined_headers = []
        for h1, h2 in zip(header_row1, header_row2):
            full_header = (h1 + "_" + h2).strip("_").replace("\n", "").replace(" ", "")
            combined_headers.append(full_header)
            
        # 결합된 헤더를 데이터프레임에 주입하고, 헤더였던 상위 2개 행은 데이터에서 삭제
        df_raw.columns = combined_headers
        df = df_raw.iloc[2:].reset_index(drop=True)
        
        # 2. 정확한 타겟 컬럼 검색 (인덱스 에러 방지를 위해 디폴트 변수 선언)
        col_sports = None
        col_time = None
        col_place = None
        
        for col in df.columns:
            # 주 종목 컬럼 찾기 (예: 스포츠활동참여_주요참여스포츠...)
            if "종목" in col and ("참여" in col or "Q3" in col):
                col_sports = col
            # 부상 시간 컬럼 찾기 (예: 스포츠활동중부상경험_부상을당한시간...)
            elif "부상" in col and "시간" in col:
                col_time = col
            # 부상 장소 컬럼 찾기 (예: 스포츠활동중부상경험_부상을당한장소...)
            elif "부상" in col and "장소" in col:
                col_place = col

        # 만약 자동 검색에 실패했을 경우를 대비한 완전 무결 방어 코드 (위치 기준)
        if not col_sports:
            col_sports = [c for c in df.columns if "종목" in c][0] if [c for c in df.columns if "종목" in c] else df.columns[3]
        if not col_time:
            col_time = [c for c in df.columns if "시간" in c][0] if [c for c in df.columns if "시간" in c] else df.columns[4]
        if not col_place:
            col_place = [c for c in df.columns if "장소" in c][0] if [c for c in df.columns if "장소" in c] else df.columns[5]

        # 3. 필요한 데이터만 정제 및 추출
        df_clean = df[[col_sports, col_time, col_place]].copy()
        
        # 숫자로 변환 (텍스트 찌꺼기 제거)
        df_clean[col_time] = pd.to_numeric(df_clean[col_time], errors='coerce')
        df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')
        df_clean = df_clean.dropna()

        # 4. [GUIDE 가이드] 코드를 직관적인 한글로 매핑
        time_map = {
            1: "새벽 (06시 미만)",
            2: "오전 (06시 ~ 12시 미만)",
            3: "오후 (12시 ~ 18시 미만)",
            4: "야간 (18시 ~ 24시 미만)",
            5: "심야 (24시 ~ 06시 미만)"
        }
        
        place_map = {
            1: "공공 체육시설 (지자체 운영 시설 등)",
            2: "민간 체육시설 (헬스장, 수영장, 요가룸 등)",
            3: "학교 체육시설 (초·중·고·대학교 운동장/체육관)",
            4: "자가 시설 (집 내부, 아파트 단지 내 시설)",
            5: "자연 환경 (등산로, 바다, 강, 야외 길거리)",
            6: "기타 장소"
        }
        
        df_clean['부상시간'] = df_clean[col_time].map(time_map)
        df_clean['부상장소'] = df_clean[col_place].map(place_map)
        df_clean['스포츠종목'] = df_clean[col_sports].astype(str).str.strip()
        
        # 유효하지 않거나 매핑되지 않은 행 최종 필터링
        df_clean = df_clean.dropna(subset=['부상시간', '부상장소'])
        df_clean = df_clean[~df_clean['스포츠종목'].str.contains('스포츠|종목|보기', na=False)]
        
        return df_clean, col_sports, col_time, col_place
        
    except Exception as e:
        st.error(f"데이터 정제 중 기술적 오류 발생: {e}")
        return pd.DataFrame(), None, None, None

# 데이터 수집 실행
data, c_sports, c_time, c_place = load_and_clean_data()

if not data.empty:
    # 사이드바 구성
    st.sidebar.header("🔍 대시보드 옵션")
    sports_list = ["전체 종목 보기"] + sorted(data['스포츠종목'].unique().tolist())
    selected_sport = st.sidebar.selectbox("종목 선택", sports_list)

    if selected_sport != "전체 종목 보기":
        filtered_df = data[data['스포츠종목'] == selected_sport]
    else:
        filtered_df = data

    # ----------------------------------------------------
    # 화면 그리기 (시각화 리포트)
    # ----------------------------------------------------
    if selected_sport == "전체 종목 보기":
        st.subheader("🏆 어떤 종목에서 부상이 가장 많이 발생할까요? (Top 10)")
        top_sports = data['스포츠종목'].value_counts().head(10).reset_index()
        top_sports.columns = ['스포츠 종목', '부상 신고 건수']
        
        fig_sports = px.bar(
            top_sports, x='부상 신고 건수', y='스포츠 종목', orientation='h',
            color='부상 신고 건수', color_continuous_scale='Reds', text_auto=True
        )
        fig_sports.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_sports, use_container_width=True)
        st.markdown("---")

    st.subheader(f"📊 {selected_sport} 부상 현황 정밀 분석")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🕒 **부상이 빈번한 시간대**")
        time_counts = filtered_df['부상시간'].value_counts().reset_index()
        time_counts.columns = ['시간대', '부상 건수']
        fig_time = px.pie(time_counts, values='부상 건수', names='시간대', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_time.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_time, use_container_width=True)
        
    with col2:
        st.markdown("### 📍 **사고 위험이 높은 장소**")
        place_counts = filtered_df['부상장소'].value_counts().reset_index()
        place_counts.columns = ['장소', '부상 건수']
        fig_place = px.bar(place_counts, x='부상 건수', y='장소', orientation='h',
                           color='부상 건수', color_continuous_scale='Blues', text_auto=True)
        fig_place.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_place, use_container_width=True)

    # 하단 텍스트 브리핑
    st.markdown("---")
    st.subheader("💡 데이터 요약 안내")
    total_count = len(filtered_df)
    if total_count > 0:
        st.info(
            f"선택하신 **[{selected_sport}]** 데이터 분석 결과, 총 **{total_count:,}건**의 안전사고 사례가 확인되었습니다.\n\n"
            f"• 부상이 가장 자주 발생하는 골든 타임은 **{filtered_df['부상시간'].mode()[0]}** 입니다.\n"
            f"• 가장 각별히 안전 조치를 취해야 할 공간은 **{filtered_df['부상장소'].mode()[0]}** 입니다."
        )
else:
    st.error("⚠️ 데이터를 불러오지 못했습니다. CSV 파일명이 `2024_스포츠_안전사고_실태조사_체육인.csv`가 맞는지 다시 한 번 확인해 주세요.")
