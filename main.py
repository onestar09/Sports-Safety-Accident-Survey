import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("🏃‍♂️ 스포츠 안전사고 데이터 시각화 대시보드")
st.markdown("어려운 설문 데이터 수치를 한글 명칭으로 변환하여 일반인들도 한눈에 보기 쉽게 보여줍니다.")

@st.cache_data
def load_and_clean_data():
    try:
        # 데이터 로드 (첫 두 행의 헤더 꼬임을 방지하기 위해 header=[0, 1] 형태로 읽거나 후처리 진행)
        df = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", low_memory=False)
        
        # 실제 데이터셋의 1번째, 2번째 행이 질문 제목이므로 이를 조합하여 컬럼을 찾습니다.
        col_sports = None
        col_time = None
        col_place = None
        
        # 파일 내부의 실제 한글 명칭을 추적하여 자동으로 찾아내는 안전 장치
        for col in df.columns:
            col_str = str(col).replace("\n", "").replace(" ", "")
            # 1. 스포츠 종목 열 찾기
            if "참여스포츠" in col_str or "종목" in col_str:
                col_sports = col
            # 2. 부상 시간 열 찾기
            elif "부상을당한시간" in col_str:
                col_time = col
            # 3. 부상 장소 열 찾기
            elif "부상을당한장소" in col_str:
                col_place = col
                
        # 만약 한글 깨짐 등으로 위 조건이 실패할 경우, 위치 기반으로 강제 지정 (방어 코드)
        if not col_sports:
            # 원본 데이터 기준 인덱스 매핑 시도
            for col in df.columns:
                if "종목" in str(df[col].iloc[0]) or "종목" in str(col):
                    col_sports = col
        
        # 최종 찾은 컬럼이 없을 때를 대비한 기본값 할당
        col_sports = col_sports if col_sports else df.columns[3]
        col_time = col_time if col_time else [c for c in df.columns if "시간" in str(c)][0]
        col_place = col_place if col_place else [c for c in df.columns if "장소" in str(c)][0]

        # 분석에 필요한 열만 복사
        df_clean = df[[col_sports, col_time, col_place]].copy()
        
        # 상단 헤더용 한글 텍스트 행이 데이터 영역에 섞여 있을 수 있으므로 숫자로 강제 변환 후 결측치 제거
        df_clean[col_time] = pd.to_numeric(df_clean[col_time], errors='coerce')
        df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')
        df_clean = df_clean.dropna()

        # [GUIDE 데이터 참고] 데이터에 저장된 숫자 코드를 일반인용 한글 문구로 매핑
        time_map = {
            1: "새벽 (06시 미만)",
            2: "오전 (06시 ~ 12시 미만)",
            3: "오후 (12시 ~ 18시 미만)",
            4: "야간 (18시 ~ 24시 미만)",
            5: "심야 (24시 ~ 06시 미만)"
        }
        
        place_map = {
            1: "공공 체육시설 (지자체 운영 시설 등)",
            2: "민간 체육시설 (일반 헬스장, 요가룸 등)",
            3: "학교 체육시설 (초·중·고·대학교 운동장 및 강당)",
            4: "자가 시설 (집 내부, 아파트 단지 내 시설)",
            5: "자연 환경 (등산로, 바다, 강, 길거리 등)",
            6: "기타 장소"
        }
        
        # 한글 이름으로 치환 및 새 컬럼 생성
        df_clean['부상시간'] = df_clean[col_time].map(time_map)
        df_clean['부상장소'] = df_clean[col_place].map(place_map)
        df_clean['스포츠종목'] = df_clean[col_sports].astype(str).str.strip()
        
        # 매핑에 실패한 유효하지 않은 데이터행 최종 정리
        df_clean = df_clean.dropna(subset=['부상시간', '부상장소'])
        # 텍스트 형태의 헤더 찌꺼기 행 제거
        df_clean = df_clean[~df_clean['스포츠종목'].str.contains('스포츠|종목|참여', na=False)]
        
        return df_clean, col_sports, col_time, col_place
        
    except Exception as e:
        st.error(f"데이터 정제 처리 과정에서 문제가 발생했습니다: {e}")
        return pd.DataFrame(), None, None, None

# 데이터 함수 작동
data, c_sports, c_time, c_place = load_and_clean_data()

if not data.empty:
    # 사이드바 설정
    st.sidebar.header("🔍 조건 선택")
    sports_list = ["전체 종목 보기"] + sorted(data['스포츠종목'].unique().tolist())
    selected_sport = st.sidebar.selectbox("비교하고 싶은 스포츠를 선택하세요", sports_list)

    if selected_sport != "전체 종목 보기":
        filtered_df = data[data['스포츠종목'] == selected_sport]
    else:
        filtered_df = data

    # ----------------------------------------------------
    # 대시보드 화면 렌더링
    # ----------------------------------------------------
    
    # 1. 메인 통계 순위 (전체 보기일 때만)
    if selected_sport == "전체 종목 보기":
        st.subheader("🏆 어떤 종목에서 부상이 가장 많이 발생했을까? (Top 10)")
        top_sports = data['스포츠종목'].value_counts().head(10).reset_index()
        top_sports.columns = ['스포츠 종목', '부상 발생 건수']
        
        fig_sports = px.bar(
            top_sports, 
            x='부상 발생 건수', 
            y='스포츠 종목', 
            orientation='h',
            color='부상 발생 건수',
            color_continuous_scale='Reds',
            text_auto=True
        )
        fig_sports.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_sports, use_container_width=True)
        st.markdown("---")

    # 2. 시간대 및 장소 비교 시각화
    st.subheader(f"📊 {selected_sport} 부상 위험 상세 분석")
    
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
            color_discrete_sequence=px.colors.qualitative.Set3
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
            color_continuous_scale='Purples',
            text_auto=True
        )
        fig_place.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_place, use_container_width=True)

    # 3. 요약 인사이트 자동화
    st.markdown("---")
    st.subheader("💡 직관적인 데이터 요약 결과")
    
    total_accidents = len(filtered_df)
    
    if total_accidents > 0:
        most_frequent_time = filtered_df['부상시간'].mode()[0]
        most_frequent_place = filtered_df['부상장소'].mode()[0]
        
        st.info(
            f"**[{selected_sport}]** 종목에 대해 조사된 총 안전사고는 **{total_accidents:,}건**입니다.\n\n"
            f"• 통계적으로 이 종목은 하루 중 **{most_frequent_time}**에 부상을 입을 확률이 가장 높습니다.\n"
            f"• 주로 사고가 일어나는 취약 공간은 **{most_frequent_place}**로 확인되었습니다. 해당 장소를 이용할 때 각별한 주의가 필요합니다."
        )
    else:
        st.warning("선택 조건에 해당하는 유효 데이터가 없습니다.")
else:
    st.error("⚠️ 데이터를 불러오는 데 실패했습니다. 파일이 스크립트와 동일한 폴더에 있는지, 이름이 정확한지 확인해 주세요.")
