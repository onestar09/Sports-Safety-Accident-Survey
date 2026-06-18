import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="2024 스포츠 안전사고 실태조사", layout="wide")

st.title("📊 스포츠 안전사고 분석 리포트")
st.markdown("전체 스포츠 종목을 통틀어 어떤 안전사고 부상이 가장 빈번하게 발생하는지 전체 항목을 합산하여 분석합니다.")

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
        
        # 2. 다중 선택으로 분리된 부상 종류 컬럼들을 모두 찾아서 매핑 및 합산
        injury_keywords = ["통증", "근육통", "염좌", "삐임", "접지름", "좌상", "타박상", "찰과상", "열상", "골절", "탈구", "뇌진탕", "부상"]
        injury_cols = []
        
        for col in df.columns:
            # 부상 증상이나 종류를 나타내는 컬럼 선별
            if "부상" in col and any(kw in col for kw in injury_keywords) and not any(x in col for x in ["시간", "장소", "종목", "이유", "원인"]):
                injury_cols.append(col)
                
        # 만약 자동 검색에 실패하면 기본 패턴 매칭 활용
        if not injury_cols:
            injury_cols = [c for c in df.columns if "부상" in c and ("부위" in c or "종류" in c or "증상" in c)]

        # 부상 종류 표준 명칭 리스트
        injury_labels = {
            "통증": "통증/근육통",
            "염좌": "염좌 (삐임/접지름)",
            "좌상": "좌상/타박상 (멍)",
            "타박": "좌상/타박상 (멍)",
            "찰과": "찰과상 (긁힘/까짐)",
            "열상": "열상 (찢어짐)",
            "골절": "골절 (뼈 부러짐)",
            "탈구": "탈구 (관절 빠짐)",
            "뇌진탕": "뇌진탕/어지러움"
        }

        injury_counts_dict = {}

        # 3. 흩어진 컬럼별로 '1' 또는 '선택' 항목 카운트 계산
        for col in injury_cols:
            # 컬럼명에서 어떤 부상인지 레이블 매칭
            matched_label = "기타 부상"
            for key, val in injury_labels.items():
                if key in col:
                    matched_label = val
                    break
            
            # 선택된 빈도 계산 (1 또는 숫자, 문자형태 모두 대응)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            count = int((df[col] == 1).sum())
            
            if count > 0:
                injury_counts_dict[matched_label] = injury_counts_dict.get(matched_label, 0) + count

        # 만약 위 방식으로 데이터가 안 묶였다면 기존 단일 컬럼 코드 보완책 작동
        if not injury_counts_dict and injury_cols:
            main_col = injury_cols[0]
            df[main_col] = pd.to_numeric(df[main_col], errors='coerce')
            raw_counts = df[main_col].value_counts()
            fallback_map = {1:"통증/근육통", 2:"염좌 (삐임/접지름)", 3:"좌상/타박상 (멍)", 4:"찰과상 (긁힘/까짐)", 5:"열상", 6:"골절", 7:"탈구", 8:"뇌진탕", 9:"기타 부상"}
            for k, v in fallback_map.items():
                if k in raw_counts:
                    injury_counts_dict[v] = int(raw_counts[k])

        # 데이터프레임으로 변환
        df_final_counts = pd.DataFrame(list(injury_counts_dict.items()), columns=['부상 종류', '발생 건수'])
        
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

    # 📈 전체 부상 종류 통합 통계 그래프 시각화
    st.subheader("🤕 대한민국 스포츠 안전사고 주요 부상 유형 통계 (전체 항목 합산)")
    
    fig_injury = px.bar(
        injury_summary, x='발생 건수', y='부상 종류', orientation='h',
        color='발생 건수', color_continuous_scale='Reds', text_auto=True
    )
    fig_injury.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="부상 발생 건수 (중복 선택 포함)",
        yaxis_title="부상 종류",
        height=600
    )
    st.plotly_chart(fig_injury, use_container_width=True)
    
    # 하단 크레딧 (푸터)
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.85rem;'>© 2024 스포츠 안전사고 실태조사 분석 대시보드 | Developed by <b>유성우, 최한별, 박건</b></p>", unsafe_allow_html=True)
else:
    st.error("⚠️ 데이터를 불러오지 못했습니다. GitHub 저장소에 CSV 파일이 실제로 업로드되어 있는지 확인해 주세요.")
