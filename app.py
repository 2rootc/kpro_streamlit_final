import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ssl
import urllib.request
from io import BytesIO

# SSL 오류 회피 (Streamlit Cloud에서 발생할 수 있음)
ssl._create_default_https_context = ssl._create_unverified_context

# 한글 폰트 설정 (Windows 환경 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.title("광역 및 지방 데이터 통합 앱 (GitHub 연동)")

# GitHub raw base URL 구성
REPO_OWNER = "2rootc"
REPO_NAME = "YOUR_REPO_NAME"  # ❀ 여기를 실제 저장소 이름으로 바꿔주세요
FILE_PATH = ""  # 예: 파일이 루트에 있으면 "", 폴더에 있으면 "data/"

RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}"

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
        url = RAW_BASE + fname
        response = urllib.request.urlopen(url)
        excel_data = BytesIO(response.read())
        dfs[key] = pd.read_excel(excel_data).iloc[1:-1, :]

    # 연도별 병합
    광역 = pd.concat([dfs["2023_광역"], dfs["2024_광역"]], ignore_index=True)
    지방 = pd.concat([dfs["2023_지방"], dfs["2024_지방"]], ignore_index=True)

    # 인덱스 설정
    광역.set_index(광역.columns[0], inplace=True)
    지방.set_index(지방.columns[0], inplace=True)

    # 통합 병합
    df = 광역.join(지방, how='outer')
    df.index = pd.to_datetime(df.index, errors='coerce')
    df = df[~df.index.isna()]

    st.success("✅ GitHub에서 데이터 불러오기 및 병합 완료!")
    st.dataframe(df.head())

except Exception as e:
    st.error(f"❌ 파일을 불러오는 도중 오류 발생: {e}")
