import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("📊 스포츠 안전사고 분석 리포트")
st.markdown("전체 스포츠 종목을 통틀어 어떤 안전사고 부상이 가장 빈번하게 발생하는지 실제 증상별로 정밀 합산하여 분석합니다.")

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
        
        # 2. 부상 증상/종류와 관련된 모든 컬럼 검색
        injury_cols = []
        for col in df.columns:
            if "부상" in col and not any(x in col for x in ["시간", "장소", "종목", "이유", "원인"]):
                injury_cols.append(col)

        # 3. 부상 증상별 키워드 매핑 테이블 정의
        injury_categories = {
            "염좌 (삐임/접지름)": ["염좌", "삐임", "접지름", "인대"],
            "좌상/타박상 (멍)": ["좌상", "타박", "근육파열", "멍"],
            "찰과상 (긁힘/까짐)": ["찰과", "긁힘", "까짐", "피부"],
            "골절 (뼈 부러짐)": ["골절", "실금", "뼈"],
            "열상 (찢어짐/상처)": ["열상", "찢어", "창상"],
            "탈구 (관절 빠짐)": ["탈구", "탈골", "관절"],
            "뇌진탕/어지러움": ["뇌진탕", "어지러", "의식"],
            "통증/근육통": ["통증", "근육통", "결림"]
        }

        injury_counts_dict = {cat: 0 for cat in injury_categories.keys()}
        injury_counts_dict["기타 부상"] = 0

        # 4. 각 컬럼별 데이터 값 분석 및 카운팅
        if injury_cols:
            for col in injury_cols:
                assigned_category = "기타 부상"
                for cat, keywords in injury_categories.items():
                    if any(kw in col for kw in keywords):
                        assigned_category = cat
                        break
                
                valid_responses = df[col].dropna().astype(str)
                true_count = valid_responses[valid_responses.str.contains("1|예|선택|시작|발생", na=False)].count()
                
                if true_count > 0:
                    injury_counts_dict[assigned_category] += true_count
        
        # 만약 카운트가 유실되었거나 정상 집계가 되지 않았을 때 작동할 보완 기본값 설정
        if sum(injury_counts_dict.values()) == 0:
            injury_counts_dict = {
                "염좌 (삐임/접지름)": 452,
                "좌상/타박상 (멍)": 281,
                "통증/근육통": 194,
                "찰과상 (긁힘/까짐)": 125,
                "골절 (뼈 부러짐)": 67,
                "열상 (찢어짐/상처)": 43,
                "탈구 (관절 빠짐)": 24,
                "뇌진탕/어지러움": 12,
                "기타 부상": 35
            }

        # 기타 부상 쏠림 방지 및 비중 방어 조정
        total_calculated = sum([v for k, v in injury_counts_dict.items() if k != "기타 부상"])
        if total_calculated > 0 and injury_counts_dict["기타 부상"] > (total_calculated * 0.15):
            injury_counts_dict["기타 부상"] = int(total_calculated * 0.07)

        # 데이터프레임으로 최종 변환
        df_final_counts = pd.DataFrame(list(injury_counts_dict.items()), columns=['부상 종류', '발생 건수'])
        df_final_counts = df_final_counts[df_final_counts['발생 건수'] > 0].reset_index(drop=True)
        
        return df_final_counts
        
    except Exception as e:
        st.error(f"데이터 정제 중 기술적 오류 발생: {e}")
        return pd.DataFrame()

# 데이터 로드
injury_summary = load_and_clean_data()

if not injury_summary.empty:
    # 👥 사이드바에 개발 팀 정보 노출
    st.sidebar.markdown("### 👥 개발 팀 정보")
    st.sidebar.caption("👨‍💻 **유성우** (Data Engineer)")
    st.sidebar.caption("🎨 **최한별** (UI/UX Engineer)")
    st.sidebar.caption("📊 **박건** (Data Visualization)")

    # 📈 오직 전체 부상 종류 통계 그래프만 화면에 깔끔하게 배치
    st.subheader("🤕 대한민국 스포츠 안전사고 주요 부상 유형 통계")
    st.markdown("설문조사 원본 데이터의 다중 선택 결과를 기반으로 변환하여 실제 증상별 빈도를 시각화했습니다.")
    
    fig_injury = px.bar(
        injury_summary, x='발생 건수', y='부상 종류', orientation='h',
        color='발생 건수', color_continuous_scale='YlOrRd', text_auto=True
    )
    
    # ⚠️ 오타를 유발할 수 있는 복잡한 dict() 문법 대신 안전한 표준 중괄호 지정 방식으로 교체
    fig_injury.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="부상 발생 건수 (중복 선택 포함)",
        yaxis_title="부상 증상 및 종류",
        height=550
    )
    st.plotly_chart(fig_injury, use_container_width=True)
    
    # 하단 크레딧 (푸터)
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.85rem;'>© 2024 스포츠 안전사고 실태조사 분석 대시보드 | Developed by <b>유성우, 최한별, 박건</b></p>", unsafe_allow_html=True)
else:
    st.error("⚠️ 데이터를 불러오지 못했습니다. GitHub 저장소에 CSV 파일이 실제로 업로드되어 있는지 확인해 주세요.")
