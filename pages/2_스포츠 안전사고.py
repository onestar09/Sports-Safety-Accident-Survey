import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2024 스포츠 및 일상 안전사고 실태조사 - 상세 분석", layout="wide")

st.title("🏥 가정 내 안전사고 부상 데이터 분석 (2페이지)")
st.markdown("집안 내부(거실, 주방 등)에서 주로 발생하는 부상 유형, 신체 손상 부위, 사고 공간별 발생 빈도를 정밀하게 분석합니다.")

@st.cache_data
def load_injury_detail_data():
    """
    제공된 정밀 분석 데이터를 기반으로 시각화용 데이터프레임을 생성합니다.
    (총 발생 건수: 460건)
    """
    # 1. 부상 유형별 데이터
    df_type = pd.DataFrame({
        "부상 유형": ["골절", "미끄러짐·넘어짐", "절단·동반", "뇌진탕", "기타"],
        "발생 건수": [215, 121, 40, 24, 60]
    })
    
    # 2. 신체 손상 부위별 데이터
    df_part = pd.DataFrame({
        "신체 부위": ["손가락·발가락", "다리·발", "팔·손", "머리·얼굴", "몸통·기타"],
        "발생 건수": [138, 114, 93, 61, 54]
    })
    
    # 3. 사고 발생 공간별 데이터
    df_space = pd.DataFrame({
        "발생 공간": ["거실", "주방", "침실", "화장실·욕실", "기타"],
        "발생 건수": [147, 110, 82, 69, 52]
    })
    
    return df_type, df_part, df_space

# 데이터 로드
df_type, df_part, df_space = load_injury_detail_data()

# 👥 사이드바에 개발 팀 정보 노출 (기존 스타일 유지)
st.sidebar.markdown("### 👥 개발 팀 정보")
st.sidebar.caption("👨‍💻 **유성우** (Data Engineer)")
st.sidebar.caption("🎨 **최한별** (UI/UX Engineer)")
st.sidebar.caption("📊 **박건** (Data Visualization)")

# 탭 구조를 활용하여 화면을 깔끔하게 분할
tab1, tab2, tab3 = st.tabs(["📊 부상 유형별", "🦵 신체 부위별", "🏠 발생 공간별"])

# --- TAB 1: 부상 유형별 ---
with tab1:
    st.subheader("📌 어떤 부상이 가장 많이 발생했을까요?")
    col1_1, col1_2 = st.columns([2, 1])
    
    with col1_1:
        fig_type = px.bar(
            df_type, x='발생 건수', y='부상 유형', orientation='h',
            color='발생 건수', color_continuous_scale='Reds', text_auto=True
        )
        fig_type.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="발생 건수 (건)",
            yaxis_title="부상 유형",
            height=400
        )
        st.plotly_chart(fig_type, use_container_width=True)
        
    with col1_2:
        st.markdown("#### **📊 유형별 요약 통계**")
        # 백분율 계산 후 테이블 노출
        df_type_pct = df_type.copy()
        df_type_pct['비중 (%)'] = (df_type_pct['발생 건수'] / df_type_pct['발생 건수'].sum() * 100).round(1)
        st.dataframe(df_type_pct, use_container_width=True, hide_index=True)
        st.caption("가장 큰 비중을 차지하는 부상은 **골절(46.7%)**이며, 미끄러짐·넘어짐이 그 뒤를 잇습니다.")

# --- TAB 2: 신체 부위별 ---
with tab2:
    st.subheader("📌 어느 부위를 가장 많이 다쳤을까요?")
    col2_1, col2_2 = st.columns([2, 1])
    
    with col2_1:
        fig_part = px.bar(
            df_part, x='발생 건수', y='신체 부위', orientation='h',
            color='발생 건수', color_continuous_scale='Oranges', text_auto=True
        )
        fig_part.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="발생 건수 (건)",
            yaxis_title="신체 부위",
            height=400
        )
        st.plotly_chart(fig_part, use_container_width=True)
        
    with col2_2:
        st.markdown("#### **🦵 부위별 요약 통계**")
        df_part_pct = df_part.copy()
        df_part_pct['비중 (%)'] = (df_part_pct['발생 건수'] / df_part_pct['발생 건수'].sum() * 100).round(1)
        st.dataframe(df_part_pct, use_container_width=True, hide_index=True)
        st.caption("말단 부위인 **손가락·발가락(30.0%)** 및 **다리·발(24.8%)**의 부상 빈도가 매우 높습니다.")

# --- TAB 3: 발생 공간별 ---
with tab3:
    st.subheader("📌 집안 어디에서 사고가 주로 일어났을까요?")
    col3_1, col3_2 = st.columns([2, 1])
    
    with col3_1:
        fig_space = px.bar(
            df_space, x='발생 건수', y='발생 공간', orientation='h',
            color='발생 건수', color_continuous_scale='Tealgrn', text_auto=True
        )
        fig_space.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="발생 건수 (건)",
            yaxis_title="사고 공간",
            height=400
        )
        st.plotly_chart(fig_space, use_container_width=True)
        
    with col3_2:
        st.markdown("#### **🏠 공간별 요약 통계**")
        df_space_pct = df_space.copy()
        df_space_pct['비중 (%)'] = (df_space_pct['발생 건수'] / df_space_pct['발생 건수'].sum() * 100).round(1)
        st.dataframe(df_space_pct, use_container_width=True, hide_index=True)
        st.caption("활동량이 많은 **거실(32.0%)**과 미끄러지기 쉬운 **주방(23.9%)**이 과반수 이상을 차지합니다.")

# 💡 하단 종합 분석 인사이트 배너
st.info(
    "💡 **데이터 분석 종합 요약**\n\n"
    "전체 460건의 데이터를 정밀 분석한 결과, 주로 **거실과 주방(합계 55.9%)** 공간에서 "
    "**미끄러지거나 넘어짐(26.3%)**으로 인해 **손가락·발가락이나 다리(합계 54.8%)** 부위에 "
    "**골절(46.7%)**을 입는 유형의 사고가 가장 치명적이고 높은 비중을 차지하고 있음을 알 수 있습니다."
)

# 하단 크레딧 (푸터) - 기존 1페이지 디자인 코드 통일
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 0.85rem;'>© 2024 스포츠 및 일상 안전사고 실태조사 분석 대시보드 | Developed by <b>유성우, 최한별, 박건</b></p>", unsafe_allow_html=True)
