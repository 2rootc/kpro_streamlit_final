import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 한글 폰트 설정 (자동 환경 감지)
import platform
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

st.title("광역 및 지방 데이터 통합 앱")

# 불러올 파일들 (xls 확장자 사용)
file_dict = {
    "2023_광역": "2023_광역.xls",
    "2023_지방": "2023_지방.xls",
    "2024_광역": "2024_광역.xls",
    "2024_지방": "2024_지방.xls"
}

# 읽기 및 병합
dfs = {}
try:
    for key, fname in file_dict.items():
        dfs[key] = pd.read_excel(fname, engine='xlrd').iloc[1:-1, :]

    # 연도별 병합
    gw = pd.concat([dfs["2023_광역"], dfs["2024_광역"]], ignore_index=True)
    lb = pd.concat([dfs["2023_지방"], dfs["2024_지방"]], ignore_index=True)

    # 인덱스 설정
    gw.set_index(gw.columns[0], inplace=True)
    lb.set_index(lb.columns[0], inplace=True)

    # 통합 병합
    df = gw.join(lb, how='outer')
    df.index = pd.to_datetime(df.index, errors='coerce')
    df = df[~df.index.isna()]

    # 컬럼명 변경
    df.columns = [
        'JW_Branch_Flow','JW_Branch_Pressure','JW_Branch_OpenRate',
        'SS_Branch_Flow','SS_Branch_Pressure',
        'STI_Branch_Flow','STI_Branch_Pressure','STI_Branch_OpenRate',
        'TA_Branch_Flow','TA_Branch_Pressure',
        'YY_Branch_Flow','YY_Branch_Pressure','YY_Branch_OpenRate',
        'MK_Branch_Flow','MK_Branch_Pressure','MK_Branch_OpenRate',
        'JW_Tank_Level#1','JW_Tank_Level#2','JW_Tank_Flow',
        'SS_Tank_Input_Flow','SS_Tank_Input_OpenRate#1','SS_Tank_Input_OpenRate#2',
        'SS_Tank_Level#1','SS_Tank_Level#2','SS_Tank_Flow',
        'STI_Tank_Input_Flow','STI_Tank_Level#1','STI_Tank_Level#2','STI_Tank_Flow',
        'TA_Tank_Input_OpenRate#1','TA_Tank_Input_OpenRate#2','TA_Tank_Level#1','TA_Tank_Level#2','TA_Tank_Flow',
        'YY_Tank_Level#1','YY_Tank_Level#2','YY_Tank_Flow',
        'MK_Tank_Level#1','MK_Tank_Level#2','MK_Tank_Flow#1(old)','MK_Tank_Flow#2(new)',
        'JM_Tank_Input_Flow','JM_Tank_Input_OpenRate#1','JM_Tank_Input_OpenRate#2',
        'JM_Tank_Level#1','JM_Tank_Level#2','JM_Tank_Flow#1(new)','JM_Tank_Flow#2(old)'
    ]

    st.success("\u2705 데이터 불러오기 및 병합 및 컬럼명 지정 완료!")
    st.dataframe(df.head())

    # object → numeric 변환
    df = df.replace({',': ''}, regex=True)
    df = df.replace({'-': pd.NA})
    df = df.apply(pd.to_numeric, errors='coerce')

    # 숫자형 데이터만 선택
    numeric_data = df.select_dtypes(include=[float, int])

    # 사용자 선택 UI (멀티셀렉트로 변경)
    selected_columns = st.multiselect("시계열 그래프로 확인할 항목을 선택하세요:", numeric_data.columns, default=numeric_data.columns[:1])

    if selected_columns:
        fig, ax = plt.subplots(figsize=(12, 5))
        for col in selected_columns:
            ax.plot(numeric_data.index, numeric_data[col], label=col)
        ax.set_title("선택된 항목 시계열 그래프")
        ax.set_xlabel('날짜')
        ax.set_ylabel('값')
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.info("📌 하나 이상의 항목을 선택해주세요.")

except ModuleNotFoundError as me:
    st.error("\u274c 필수 라이브러리가 설치되어 있지 않습니다. requirements.txt 또는 pip install 로 누락된 패키지를 설치하세요.")
    st.code(str(me))
except Exception as e:
    st.error("\u274c 파일을 불러오는 도중 오류 발생: " + str(e))
