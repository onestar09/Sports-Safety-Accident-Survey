import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(page_title="스포츠 안전사고 대시보드", layout="wide")
st.title("📊 스포츠 안전사고 실태조사 데이터 대시보드")

@st.cache_data
def load_and_clean_data():
    try:
        # 데이터 파일 로드
        df_raw = pd.read_csv("2024_스포츠_안전사고_실태조사_체육인.csv", header=None, low_memory=False)
        
        # 2줄 헤더 병합 처리
        h1 = df_raw.iloc[0].fillna("").astype(str)
        h2 = df_raw.iloc[1].fillna("").astype(str)
        
        headers = []
        for a, b in zip(h1, h2):
            full = (a + "_" + b).strip("_").replace("\n", "").replace(" ", "")
            headers.append(full)
            
        df_raw.columns = headers
        df = df_raw.iloc[2:].reset_index(drop=True)
        
        # 컬럼 자동 검색
        col_sports = None
        col_place = None
        
        for c in df.columns:
            if ("SQ2" in c or "종목" in c) and ("참여" in c or "주요" in c or "SQ2" in c):
                col_sports = c
                break
        for c in df.columns:
            if "부상" in c and "장소" in c:
                col_place = c
                break

        if not col_sports:
            col_sports = df.columns[3]
        if not col_place:
            col_place = df.columns[5]

        # 시간대 컬럼 및 부상 부위 컬럼 인덱스 정의
        time_cols = [df_raw.columns[i] for i in range(597, 605)]
        time_labels = [str(df_raw.iloc[1, i]).strip() for i in range(597, 605)]
        
        injury_cols = [df_raw.columns[i] for i in range(23, 61)]
        injury_labels = [str(df_raw.iloc[1, i]).replace("부상 부위_", "").strip() for i in range(23, 61)]

        df_clean = df.copy()
        df_clean[col_sports] = pd.to_numeric(df_clean[col_sports], errors='coerce')
        df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')

        # 데이터 매핑 딕셔너리 생성
        raw_sports = [
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
        
        sports_map = {}
        for idx, name in enumerate(raw_sports):
            sports_map[idx + 1] = name
            
        place_map = {
            1: "공공 체육시설", 2: "민간 체육시설", 3: "학교 체육시설",
            4: "자가 시설", 5: "자연 환경", 6: "기타 장소"
        }
        
        df_clean['스포츠종목'] = df_clean[col_sports].map(sports_map)
        df_clean['부상장소'] = df_clean[col_place].map(place_map)
        
        df_clean = df_clean.dropna(subset=['스포츠종목', '부상장소'])
        df_clean = df_clean[df_clean['스포츠종목'] != "없음"]
        
        return df_clean, time_cols, time_labels, injury_cols, injury_labels
        
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return pd.DataFrame(), [], [], [], []

# 데이터 실행 및 반환
data, time_cols, time_labels, injury_cols, injury_labels = load_and_clean_data()

if not data.empty:
    # ----------------------------------------------------
    # 사이드바 설정 (개발자 정보 추가 영역)
    # ----------------------------------------------------
    st.sidebar.header("⚙️ 옵션")
    sports_list = ["전체 종목 보기"] + sorted(data['스포츠종목'].unique().tolist())
    selected_sport = st.sidebar.selectbox("종목 선택", sports_list)

    # 사이드바 하단에 개발자 정보 깔끔하게 배치
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👥 개발 팀 정보")
    st.sidebar.caption("👨‍💻 **유성우** (Data Engineer)")
    st.sidebar.caption("🎨 **최한별** (UI/UX Engineer)")
    st.sidebar.caption("📊 **박건** (Data Visualization)")

    if selected_sport != "전체 종목 보기":
        filtered_df = data[data['스포츠종목'] == selected_sport]
    else:
        filtered_df = data

    # 탭 메뉴 분할
    tab1, tab2 = st.tabs(["🏠 1페이지: 기본 현황", "🩹 2페이지: 부상 부위 비교"])

    # 1페이지 영역
    with tab1:
        if selected_sport == "전체 종목 보기":
            st.subheader("🏆 종목별 부상 발생 건수 (Top 10)")
            top_sports = data['스포츠종목'].value_counts().head(10).reset_index()
            top_sports.columns = ['스포츠 종목', '건수']
            fig1 = px.bar(top_sports, x='건수', y='스포츠 종목', orientation='h', text_auto=True)
            st.plotly_chart(fig1, use_container_width=True)
            
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🕒 부상 시간대")
            t_dict = {}
            for c, l in zip(time_cols, time_labels):
                t_dict[l] = filtered_df[c].dropna().count()
            t_df = pd.DataFrame(list(t_dict.items()), columns=['시간대', '건수'])
            fig2 = px.pie(t_df, values='건수', names='시간대', hole=0.3)
            st.plotly_chart(fig2, use_container_width=True)
            
        with col2:
            st.markdown("### 📍 부상 장소")
            p_df = filtered_df['부상장소'].value_counts().reset_index()
            p_df.columns = ['장소', '건수']
            fig3 = px.bar(p_df, x='건수', y='장소', orientation='h', text_auto=True)
            st.plotly_chart(fig3, use_container_width=True)

    # 2페이지 영역
    with tab2:
        st.subheader("🩹 신체 부위별 부상 발생 빈도 비교")
        
        injury_dict = {}
        for c, l in zip(injury_cols, injury_labels):
            if "내용" not in l:
                injury_dict[l] = filtered_df[c].dropna().count()
                
        injury_df = pd.DataFrame(list(injury_dict.items()), columns=['부상 부위', '부상 건수'])
        
        # 비율 계산 및 정렬
        total_cases = filtered_df[injury_cols].notnull().any(axis=1).sum()
        if total_cases > 0:
            injury_df['비율(%)'] = ((injury_df['부상 건수'] / total_cases) * 100).round(1)
        else:
            injury_df['비율(%)'] = 0.0
            
        injury_df = injury_df.sort_values(by='부상 건수', ascending=True).reset_index(drop=True)
        top_injury = injury_df[injury_df['부상 건수'] > 0].tail(15)
        
        if not top_injury.empty:
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown("#### **📊 최다 부상 부위 비교 차트**")
                fig4 = px.bar(top_injury, x='부상 건수', y='부상 부위', orientation='h', 
                              text='비율(%)', color='부상 건수', color_continuous_scale='Oranges')
                fig4.update_traces(texttemplate='%{text}%', textposition='outside')
                st.plotly_chart(fig4, use_container_width=True)
            with c2:
                st.markdown("#### **📋 부상 순위 전체 데이터 통계**")
                show_df = injury_df.sort_values(by='부상 건수', ascending=False).reset_index(drop=True)
                show_df.index = show_df.index + 1
                st.dataframe(show_df, use_container_width=True, height=400)
        else:
            st.info("해당 조건에 집계된 부상 부위 데이터가 없습니다.")

    # ----------------------------------------------------
    # 대시보드 화면 맨 하단 푸터(Footer) 공통 배치
    # ----------------------------------------------------
    st.markdown("---")
    st.center = st.markdown(
        "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
        "© 2024 스포츠 안전사고 실태조사 분석 대시보드 | Developed by 유성우, 최한별, 박건"
        "</p>", 
        unsafe_allow_html=True
    )

else:
    st.error("데이터 파일 로드에 실패했습니다. 경로와 파일명을 확인해 주세요.")
