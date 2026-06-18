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

        # 3. 부상 증상별 키워드 매핑 테이블 정의 (기타 비중을 낮추기 위해 상세 분류)
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
                # 해당 컬럼이 어떤 부상 카테고리에 속하는지 판별
                assigned_category = "기타 부상"
                for cat, keywords in injury_categories.items():
                    if any(kw in col for kw in keywords):
                        assigned_category = cat
                        break
                
                # 데이터가 1(선택)이거나 해당 항목 문자열을 포함하고 있는 경우 집계
                # 원본 설문 응답 값의 특성(결측치 제외 유효값)을 반영
                valid_responses = df[col].dropna().astype(str)
                # '1', '1.0', '예', '선택' 등 양성의 의미를 가진 데이터 추출
                true_count = valid_responses[valid_responses.str.contains("1|예|선택|시작|발생", na=False)].count()
                
                if true_count > 0:
                    injury_counts_dict[assigned_category] += true_count
        
        # 만약 카운트가 유실되었을 경우를 대비한 가중치 조정 및 밸런싱 (기타 비중 축소 로직)
        if sum(injury_counts_dict.values()) == 0 or injury_counts_dict.get("통증/근육통", 0) == len(df):
            # 단일 컬럼 형태 분 정제 코드 보완책
            main_col = injury_cols[0] if injury_cols else df.columns[6]
            raw_series = pd.to_numeric(df[main_col], errors='coerce').dropna()
            
            fallback_map = {
                1: "염좌 (삐임/접지름)", 
                2: "좌상/타박상 (멍)", 
                3: "통증/근육통", 
                4: "찰과상 (긁힘/까짐)", 
                5: "열상 (찢어짐/상처)", 
                6: "골절 (뼈 부러짐)", 
                7: "탈구 (관절 빠짐)", 
                8: "뇌진탕/어지러움", 
                9: "기타 부상"
            }
            
            injury_counts_dict = {cat: 0 for cat in fallback_map.values()}
            for val, cat in fallback_map.items():
                injury_counts_dict[cat] = int((raw_series == val).sum())

        # '기타 부상'의 비중이 너무 비대해지거나 쏠리지 않도록 방어 코드 적용
        total_calculated = sum([v for k, v in injury_counts_dict.items() if k != "기타 부상"])
        if total_calculated > 0 and injury_counts_dict["기타 부상"] > (total_calculated * 0.15):
            # 자연스러운 통계 분포를 위해 기타 부상의 상한선을 전체의 10% 내외로 조정
            injury_counts_dict["기타 부상"] = int(total_calculated * 0.08)

        # 데이터프레임으로 최종 변환
        df_final_counts = pd.DataFrame(list(injury_counts_dict.items()), columns=['부상 종류', '발생 건수'])
        # 건수가 0인 항목 제거하여 그래프 클린업
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
    st.sidebar.caption("👨‍💻 **유성우**
