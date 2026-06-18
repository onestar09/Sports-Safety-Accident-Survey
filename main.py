import pandas as pd

# 1. 데이터 불러오기
file_path = "2024_스포츠_안전사고_실태조사_체육인.csv"
df = pd.read_csv(file_path, low_memory=False)

# 데이터 추출 기준 설정 (질문지 라벨 제외, 3번째 행부터 실제 데이터)
data_df = df.iloc[3:].copy()


# =====================================================================
# [항목 1] 성별 분석 (단일 선택 예시)
# =====================================================================
print("-" * 50)
print("■ 성별 부상 발생 현황")
if 'SQ3' in df.columns:
    gender_counts = data_df['SQ3'].value_counts()
    gender_labels = { '1': '남성', '2': '여성' } # 설문지 가이드 기준 매핑
    
    for val, count in gender_counts.items():
        label = gender_labels.get(str(val), f"기타({val})")
        percentage = (count / len(data_df) * 100).round(1)
        print(f"- {label}: {count}명 ({percentage}%)")
else:
    print("성별(SQ3) 컬럼을 찾을 수 없습니다.")


# =====================================================================
# [항목 2] 연령대 분석 (단일 선택 예시)
# =====================================================================
print("-" * 50)
print("■ 연령대별 부상 발생 현황")
if 'SQ4' in df.columns:
    age_counts = data_df['SQ4'].value_counts().sort_index()
    age_labels = {
        '1': '12세 이하', '2': '13~18세 이하', '3': '19~29세 이하', 
        '4': '30대', '5': '40대', '6': '50대', '7': '60~64세 이하', '8': '65세 이상'
    }
    for val, count in age_counts.items():
        label = age_labels.get(str(val), f"기타({val})")
        percentage = (count / len(data_df) * 100).round(1)
        print(f"- {label}: {count}명 ({percentage}%)")
else:
    print("연령대(SQ4) 컬럼을 찾을 수 없습니다.")


# =====================================================================
# [항목 3] 부상이 빈번한 시간대 분석 (★오류 수정 반영 파트★)
# =====================================================================
print("-" * 50)
print("■ 부상이 빈번한 시간대 분석 (다중 응답 반영)")

# 부상을 당한 시간대에 해당하는 597번째부터 604번째 컬럼 지정
time_columns = df.columns[597:605]
time_labels = [df.iloc[1, idx] for idx in range(597, 605)] # 행 1에서 '새벽 시간대' 등 추출

# 시간대별 실제 응답 데이터 집계
time_counts = {}
for idx, col in enumerate(time_columns):
    label = time_labels[idx]
    # 각 시간대별로 체크(값이 존재)된 행의 개수 계산
    count = data_df[col].dropna().count()
    time_counts[label] = count

# 시간대 질문에 하나라도 응답한 전체 유효 응답자 수
total_time_respondents = data_df[time_columns].notnull().any(axis=1).sum()

if total_time_respondents > 0:
    # 데이터프레임 변환 및 비율 계산
    injury_time_df = pd.DataFrame(list(time_counts.items()), columns=['시간대', '빈도(건)'])
    injury_time_df['비율(%)'] = ((injury_time_df['빈도(건)'] / total_time_respondents) * 100).round(1)
    
    # 빈도 높은 순으로 정렬하여 출력
    injury_time_df = injury_time_df.sort_values(by='빈도(건)', ascending=False).reset_index(drop=True)
    
    for idx, row in injury_time_df.iterrows():
        print(f" {idx+1}위. {row['시간대']}: {row['빈도(건)']}건 ({row['비율(%)']})")
    print(f"* 비율 산출 기준 총 부상 시점 수: {total_time_respondents}건")
else:
    print("시간대 데이터에 접근할 수 없거나 유효한 응답이 없습니다.")


# =====================================================================
# [항목 4] 부상 발생 장소 분석 (예시 항목)
# =====================================================================
print("-" * 50)
print("■ 주요 부상 발생 장소 현황")
# 기존 코드 구조에 맞춰 장소 데이터 컬럼이 있다면 추가 작성되는 영역입니다.
# (예시 코드 종료)
print("-" * 50)
