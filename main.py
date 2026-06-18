import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("📊 스포츠 안전사고 데이터 시각화 대시보드")
st.markdown("설문지의 숫자 코드를 일반인들이 알기 쉬운 종목 명칭과 항목들로 자동 변환하여 보여줍니다.")

@st.cache_data
def load_and_clean_data():
    try:
        # 🔍 파일명이 .csv 인지 .csv.csv 인지 자동으로 체크하여 존재하는 파일을 로드합니다.
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
        
        # 2. 타겟 컬럼 검색
        col_sports = None
        col_time_detail = None  # 1시간 단위 상세 시간 컬럼
        col_place = None
        
        for col in df.columns:
            if ("SQ2" in col or "종목" in col) and ("참여" in col or "주요" in col or "SQ2" in col):
                col_sports = col
                break
        
        for col in df.columns:
            # 기존 대분류 시간대 대신 '시' 혹은 구체적인 시간 코드가 들어간 세부 시간 컬럼 탐색
            if "부상" in col and ("시" in col or "시간" in col) and "대분류" not in col:
                col_time_detail = col
            if "부상" in col and "장소" in col:
                col_place = col

        if not col_sports:
            col_sports = [c for c in df.columns if "SQ2" in c or "종목" in c][0] if [c for c in df.columns if "SQ2" in c or "종목" in c] else df.columns[3]
        if not col_time_detail:
            # 상세 시간 컬럼을 못 찾을 경우 기존 시간 컬럼을 대안으로 지정
            col_time_detail = [c for c in df.columns if "시간" in c or "시" in c][0] if [c for c in df.columns if "시간" in c or "시" in c] else df.columns[4]
        if not col_place:
            col_place = [c for c in df.columns if "장소" in c][0] if [c for c in df.columns if "장소" in c] else df.columns[5]

        # 3. 필요한 데이터 추출 및 숫자형 변환
        df_clean = df[[col_sports, col_time_detail, col_place]].copy()
        df_clean[col_sports] = pd.to_numeric(df_clean[col_sports], errors='coerce')
        df_clean[col_time_detail] = pd.to_numeric(df_clean[col_time_detail], errors='coerce')
        df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')
        df_clean = df_clean.dropna()

        # 4. 종목 매핑 사전
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
        
        # 장소 매핑
        place_map = {
            1: "공공 체육시설 (지자체 운영 시설 등)",
            2: "민간 체육시설 (헬스장, 수영장, 요가룸 등)",
            3: "학교 체육시설 (초·중·고·대학교 운동장/체육관)",
            4: "자가 시설 (집 내부, 아파트 단지 내 시설)",
            5: "자연 환경 (등산로, 바다, 강, 야외 길거리)",
            6: "기타 장소"
        }
        
        # 1시간 단위 레이블 자동 생성 사전
        hourly_map = {}
        for hour in range(0, 25):
            hourly_map[hour] = f"{hour:02d}시 ~ {hour+1:02d}시"
            
        # 데이터 치환
        df_clean['스포츠종목'] = df_clean[col_sports].map(sports_map)
        df_clean['상세부상시간'] = df_clean[col_time_detail].map(hourly_map).fillna(df_clean[col_time_detail].astype(str) + "시")
        df_clean['부상장소'] = df_clean[col_place].map(place_map)
        
        # 매핑되지 않은 데이터 최종 정리
        df_clean = df_clean.dropna(subset=['스포츠종목', '상세부상시간', '부상장소'])
        df_clean = df_clean[df_clean['스포츠종목'] != "없음"]
        
        return df_clean, col_sports
        
    except Exception as e:
        st.error(f"데이터 정제 중 기술적 오류 발생: {e}")
        return pd.DataFrame(), None

# 데이터 변환 함수 실행
data, final_col_name = load_and_clean_data()

if not data.empty:
    # 사이드바 구성
    st.sidebar.header("🔍 대시보드 옵션")
    sports_list = ["전체 종목 보기"] + sorted(data['스포츠종목'].unique().tolist())
    selected_sport = st.sidebar.selectbox("종목 선택", sports_list)

    # 👥 사이드바 하단 개발 팀 정보 배치
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👥 개발 팀 정보")
    st.sidebar.caption("👨‍💻 **유성우** (Data Engineer)")
    st.sidebar.caption("🎨 **최한별** (UI/UX Engineer)")
    st.sidebar.caption("📊 **박건** (Data Visualization)")

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
    
    # 🕒 1시간 마다 발생하는 건수의 비율을 나타내는 원그래프 (오타 수정 완료)
    with col1:
        st.markdown("### 🕒 **1시간 단위별 부상 발생 비율**")
        
        # 1시간 단위 빈도 계산 및 비율 데이터 생성
        hourly_counts = filtered_df['상세부상시간'].value_counts().reset_index()
        hourly_counts.columns = ['시간대', '발생 건수']
        
        # 데이터 정렬 (시간 순서 정렬)
        hourly_counts = hourly_counts.sort_values('시간대')
        
        # 원그래프(도넛) 시각화 생성
        fig_time_pie = px.pie(
            hourly_counts, values='발생 건수', names='시간대', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.muted  # 소문자 'muted'로 교체 완료
        )
        # 그래프 내부 레이블에 퍼센트(비율)와 시간대 정보 동시 노출
        fig_time_pie.update_traces(textinfo='percent+label')
        fig_time_pie.update_layout(
            legend_title_text="상세 시간대별 분류",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_time_pie, use_container_width=True)
        
    with col2:
        st.markdown("### 📍 **사고 위험이 높은 장소**")
        place_counts = filtered_df['부상장소'].value_counts().reset_index()
        place_counts.columns = ['장소', '부상 건수']
        fig_place = px.bar(place_counts, x='부상 건수', y='장소', orientation='h',
                           color='부상 건수', color_continuous_scale='Blues', text_auto=True)
        fig_place.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_place, use_container_width=True)

    # 하단 텍스트 자동 요약 브리핑
    st.markdown("---")
    st.subheader("💡 데이터 요약 안내")
    total_count = len(filtered_df)
    if total_count > 0:
        st.info(
            f"선택하신 **[{selected_sport}]** 데이터 분석 결과, 총 **{total_count:,}건**의 안전사고 사례가 확인되었습니다.\n\n"
            f"• 1시간 단위 비율 분석 결과, 사고가 가장 집중적으로 터지는 시간대는 **{filtered_df['상세부상시간'].mode()[0]}** 입니다.\n"
            f"• 가장 각별히 안전 조치를 취해야 할 공간은 **{filtered_df['부상장소'].mode()[0]}** 입니다."
        )

    # 📜 화면 최하단 공통 푸터(Footer) 크레딧 배치
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: gray; font-size: 0.85rem; margin-top: 20px;'>",
        unsafe_allow_html=True
    )
    st.markdown(
        "© 2024 스포츠 안전사고 실태조사 분석 대시보드 | Developed by <b>유성우, 최한별, 박건</b>",
        unsafe_allow_html=True
    )
    st.markdown(
        "</p>",
        unsafe_allow_html=True
    )
else:
    st.error("⚠️ 데이터를 불러오지 못했습니다. GitHub 저장소에 CSV 파일이 실제로 업로드되어 있는지 확인해 주세요.")
