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

        # 3. [시간대 다중 응답 매핑 처리] - 597번째부터 604번째 열까지 안전 추출
        # 설문지 행 1에서 실제 라벨('새벽 시간대', '오후 시간대' 등) 가져오기
        time_cols_indices = range(597, 605)
        time_cols = [df_raw.columns[i] for i in time_cols_indices]
        time_labels = [str(df_raw.iloc[1, i]).strip() for i in time_cols_indices]
        
        # 기본 데이터 정제 및 변환
        df_clean = df.copy()
        df_clean[col_sports] = pd.to_numeric(df_clean[col_sports], errors='coerce')
        df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')

        # 4. 맵 사전 정의
        raw_sports_list = [
            "가라테", "검도", "게이트볼", "골프(스크린골프 포함)", "국학기공",
            "궁도", "그라운드골프", "근대5종", "농구", "당구(포켓볼 포함)",
            "댄스스포츠", "럭비", "레슬링", "롤러(인라인스케이트/하키 등)", "루지",
            "바둑", "바이애슬론", "배구", "배드민턴", "보디빌딩(헬스)",
            "복싱(권투)", "볼링", "봅슬레이/스켈레톤", "빙상(스케이트/피겨 등)", "사격",
            "산악(등산, 클라이밍 등)", "세팍타크로", "소프트테니스(정구)", "수상스키/웨이크보드", 
            "수영(수중발레, 다이빙, 수구 등)", "스쿼시", "스키/스노우보드", "승마", "씨름", 
            "아이스하키", "야구/소프트볼", "양궁", "에어로빅", "역도", "요트",
            "우슈", "유도", "육상(단거리/마라톤/조깅 등)", "자전거(사이클/MTB 등)", "조정",
            "족구", "주짓수", "줄넘기", "철인3종(트라이애슬론)", "체조(맨손/생활체조 등)",
            "축구", "카누", "컬링", "탁구", "태권도",
            "택견", "테니스", "파크골프", "패러글라이딩(행글라이딩)", "펜싱",
            "핀수영", "하키(필드하키)", "합기도", "핸드볼", "없음"
        ]
        sports_map = {i + 1: name for i, name in enumerate(raw_sports_list)}
        
        place_map = {
            1: "공공 체육시설",
            2: "민간 체육시설",
            3: "학교 체육시설",
            4: "자가 시설",
            5: "자연 환경 (등산로, 강, 바다 등)",
            6: "기타 장소"
        }
        
        # 텍스트 명칭 치환
        df_clean['스포츠종목'] = df_clean[col_sports].map(sports_map)
        df_clean['부상장소'] = df_clean[col_place].map(place_map)
        
        # 유효 데이터 필터링
        df_clean = df_clean.dropna(subset=['스포츠종목', '부상장소'])
        df_clean = df_clean[df_clean['스포츠종목'] != "없음"]
        
        # 메인 가독성을 위해 시간대 매핑 정보와 다중 컬럼명 리스트를 함께 반환
        return df_clean, col_sports, time_cols, time_labels
        
    except Exception as e:
        st.error(f"데이터 정제 중 기술적 오류 발생: {e}")
        return pd.DataFrame(), None, [], []

# 데이터 변환 함수 실행
data, final_col_name, time_cols, time_labels = load_and_clean_data()

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
    # 시각화 리포트 화면 구성
    # ----------------------------------------------------
    if selected_sport == "전체 종목 보기":
        st.subheader("🏆 어떤 스포츠 종목에서 부상이 가장 많이 발생할까요? (Top 10)")
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
        
        # ★ 다중 선택 컬럼 집계 연산 파트 ★
        time_counts_dict = {}
        for col, label in zip(time_cols, time_labels):
            # 체크되어 데이터가 존재하는 행의 개수를 집계
            cnt = filtered_df[col].dropna().count()
            time_counts_dict[label] = cnt
            
        time_counts = pd.DataFrame(list(time_counts_dict.items()), columns=['시간대', '부상 건수'])
        
        # 도넛 차트 시각화
        fig_time = px.pie(time_counts, values='부상 건수', names='시간대', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_time.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_time, use_container_width=True)
        
    with col2:
        st.markdown("### 📍 **사고 위험이 높은 장소**")
        place_counts = filtered_df['부상장소'].value_counts().reset_index()
