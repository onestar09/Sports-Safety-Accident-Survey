import streamlit as st
import pandas as pd
import plotly.express as px

# Streamlit 설정
st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("📊 스포츠 안전사고 데이터 시각화 대시보드")
st.markdown("설문지 데이터를 직관적인 종목 명칭과 항목들로 자동 변환하여 보여줍니다.")

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

        # 3. 시간대 다중 응답 설정 (597~604번째 열)
        time_cols_indices = range(597, 605)
        time_cols = [df_raw.columns[i] for i in time_cols_indices]
        time_labels = [str(df_raw.iloc[1, i]).strip() for i in time_cols_indices]
        
        # 4. 부상 부위 다중 응답 설정 (23~60번째 열 자동 추출)
        injury_cols_indices = range(23, 61)
        injury_cols = [df_raw.columns[i] for i in injury_cols_indices]
        injury_labels = [str(df_raw.iloc[1, i]).replace("부상 부위_", "").strip() for i in injury_cols_indices]

        # 기본 데이터 정제 및 변환
        df_clean = df.copy()
        df_clean[col_sports] = pd.to_numeric(df_clean[col_sports], errors='coerce')
        df_clean[col_place] = pd.to_numeric(df_clean[col_place], errors='coerce')

        # 5. 종목 및 장소 마스킹 리스트 정의
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
        
        sports_map = {}
        for i, name in enumerate(raw_sports_list):
            sports_map[i + 1] = name
        
        place_map = {
            1: "공공 체육시설", 2: "민간 체육시설", 3: "학교 체육시설",
            4: "자가 시설", 5: "자연 환경 (등산로, 강, 바다 등)", 6: "기타 장소"
        }
        
        df_clean['스포츠종목'] = df_clean[col_sports].map(sports_map)
        df_clean['부상장소'] = df_clean[col_place].map(place_map)
        
        df_clean = df_clean.dropna(subset=['스포츠종목', '부상장소'])
        df_clean = df_clean[df_clean['스포츠종목'] != "없음"]
        
        return df_clean, col_sports, time_cols, time_labels, injury_cols, injury_labels
        
    except Exception as e:
        st.error(f"데이터 정제 중 기술적 오류 발생: {e}")
        return pd.DataFrame(), None, [], [], [], []

# 데이터 변환 실행
data, final_col_name, time_cols, time_labels, injury_cols, injury_labels = load_and_clean_data()

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
    # 페이지 분할을 위한 대시보드 탭(Tabs) 생성
    # ----------------------------------------------------
    tab1, tab2 = st.tabs(["🏠 기본 현황 분석", "🤕 2페이지: 신체 부위별 부상 비교"])

    # ====================================================
    # [1페이지 탭] 기본 현황 분석
    # ====================================================
    with tab1:
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
            
            time_counts_dict = {}
            for col, label in zip(time_cols, time_labels):
                time_counts_dict[label] = filtered_df[col].dropna().count()
                
            time_counts = pd.DataFrame(list(time_counts_dict.items()), columns=['시간대', '부상 건수'])
            
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

        # 하단 텍스트 자동 요약 브리핑
        st.markdown("---")
        st.subheader("💡 데이터 요약 안내")
        total_count = len(filtered_df)
        
        if total_count > 0:
            highest_time = time_counts.sort_values(by='부상 건수', ascending=False).iloc[0]['시간대']
            highest_place = place_counts.sort_values(by='부상 건수', ascending=False).iloc[0]['장소'] if not place_counts.empty else "알 수 없음"
            
            st.info(
                f"선택하신 [{selected_sport}] 데이터 분석 결과, 설문 참여자 중 총 {total_count:,}명의 데이터가 조회되었습니다. "
                f"부상이 가장 자주 발생하는 시간대는 {highest_time} 이며, "
                f"가장 안전 조치를 취해야 할 공간은 {highest_place} 입니다."
            )

    # ====================================================
    # [2페이지 탭] 신체 부위별 부상 비교
    # ====================================================
    with tab2:
        st.subheader(f"🩹 {selected_sport} 신체 부위별 부상 위험도 비교")
        st.markdown("스포츠 활동 중 어느 신체 부위를 가장 많이 다치는지 보여주는 그래프 영역입니다.")
        
        # 다중 응답 데이터를 프레임으로 가공 처리
        injury_counts_dict = {}
        for col, label in zip(injury_cols, injury_labels):
            if "내용" not in label:
                cnt = filtered_df[col].dropna().count()
                injury_counts_dict[label] = cnt
        
        injury_df = pd.DataFrame(list(injury_counts_dict.items()), columns=['신체 부위', '부상 발생 빈도(건)'])
        
        # 총 부상 보고자 수 기준 비율 계산
        total_injury_cases = filtered_df[injury_cols].notnull().any(axis=1).sum()
        if total_injury_cases > 0:
            injury_df['발생 비율(%)'] = ((injury_df['부상 발생 빈도(건)'] / total_injury_cases) * 100).round(1)
        else:
            injury_df['발생 비율(%)'] = 0.0
            
        # 데이터가 있는 부위 위주 상위 15개 슬라이싱 정렬
        injury_df = injury_df.sort_values(by='부상 발생 빈도(건)', ascending=True).reset_index(drop=True)
        top_injury_df = injury_df[injury_df['부상 발생 빈도(건)'] > 0].tail(15)
        
        if not top_injury_df.empty:
            sub_col1, sub_col2 = st.columns([3, 2])
            
            with sub_col1:
                st.markdown("#### **📊 주요 부상 부위 순위 그래프**")
                fig_injury = px.bar(
                    top_injury_df, x='부상 발생 빈도(건)', y='신체 부위', orientation='h',
                    color='부상 발생 빈도(건)', color_continuous_scale='Oranges',
                    text='발생 비율(%)', hover_data=['발생 비율(%)']
                )
                fig_injury.update_traces(texttemplate='%{text}%', textposition='outside')
                fig_injury.update_layout(
                    xaxis_title="부상 빈도 (건수)",
                    yaxis_title="부상 발생 부위",
                    margin=dict(l=100, r=40, t=20, b=20)
                )
                st.plotly_chart(fig_injury, use_container_width=True)
                
            with sub_col2:
                st.markdown("#### **📋 부상 부위 통계표 (상위순)**")
                display_df = injury_df.sort_values(by='부상 발생 빈도(건)', ascending=False).reset_index(drop=True)
                display_df.index = display_df.index + 1
                st.dataframe(display_df, use_container_width=True, height=450)
                
            # 데이터 통계 브리핑 추가
            most_damaged_part = display_df.iloc[0]['신체 부위']
            most_damaged_pct = display_df.iloc[0]['발생 비율(%)']
            st.warning(
                f"💡 부상 부위 통계 브리핑: "
                f"[{selected_sport}] 종목에서 가장 많은 부상이 집계된 신체 부위는 {most_damaged_part} 이며, "
                f"해당 종목 부상자의 약 {most_damaged_pct}% 가 이 부위에 부상을 입은 것으로 분석됩니다."
            )
        else:
            st.info("선택한 조건에서는 수집된 신체 부위별 부상 데이터 빈도가 0건입니다.")

else:
    st.error("⚠️ 데이터를 불러오지 못했습니다. CSV 파일명이 정확한지 확인해 주세요.")
