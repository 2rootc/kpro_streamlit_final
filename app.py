import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 한글 폰트 설정 (Windows 환경 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.title("광역 및 지방 데이터 통합 앱")

# 불러올 파일들
file_dict = {
    "2023_광역": "2023_광역.xlsx",
    "2023_지방": "2023_지방.xlsx",
    "2024_광역": "2024_광역.xlsx",
    "2024_지방": "2024_지방.xlsx"
}

# 읽기 및 병합
dfs = {}
try:
    for key, fname in file_dict.items():
        dfs[key] = pd.read_excel(fname).iloc[1:-1, :]

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

    st.success("\u2705 데이터 불러오기 및 병합 완료!")
    st.dataframe(df.head())

except ModuleNotFoundError as me:
    st.error("\u274c 필수 라이브러리가 설치되어 있지 않습니다. requirements.txt 또는 pip install 로 누락된 패키지를 설치하세요.")
    st.code(str(me))
except Exception as e:
    st.error("\u274c 파일을 불러오는 도중 오류 발생: " + str(e))
