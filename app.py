import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 한글 폰트 설정 (자동 환경 감지)
import platform
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

st.title("용수수요량 예측 시뮬레이션")

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

    # MK 및 JM 유량 처리
    cutoff = pd.to_datetime("2024-09-23 15:00")
    df['MK_Tank_Flow'] = np.where(
        df.index < cutoff,
        df['MK_Tank_Flow#1(old)'],
        df['MK_Tank_Flow#2(new)']
    )
    df.drop(['MK_Tank_Flow#1(old)', 'MK_Tank_Flow#2(new)'], axis=1, inplace=True)
    df.drop(columns=['JM_Tank_Flow#1(new)'], inplace=True)
    df.rename(columns={'JM_Tank_Flow#2(old)': 'JM_Tank_Flow'}, inplace=True)

    # 기준 시점 이후 데이터 제거
    cutoff = pd.to_datetime("2024-10-19 00:00")
    df = df[df.index < cutoff]

    # object → numeric 변환
    df = df.replace({',': ''}, regex=True)
    df = df.replace({'-': pd.NA})
    df = df.apply(pd.to_numeric, errors='coerce')

    # 이상치 제거 및 전처리
    processed_df = df.copy()
    from sklearn.preprocessing import StandardScaler
    scaler_standard = StandardScaler()

    # 전처리 대상 컬럼: flow, level 포함
    target_columns = [col for col in processed_df.columns if any(kw in col.lower() for kw in ['flow', 'level'])]

    for col in target_columns:
        series = processed_df[col]

        # 1. 음수 제거 (flow에만)
        if 'flow' in col.lower():
            series = series.mask(series < 0, np.nan)

        # 2. 이상치 제거 (IQR 방식)
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        series = series.mask((series < lower) | (series > upper), np.nan)

        # 3. 결측값 보간
        series = series.interpolate(method='linear', limit_direction='both')

        # 4. 수위(level)만 표준화하고 원본에 덮어쓰기
        if 'level' in col.lower():
            series = scaler_standard.fit_transform(series.values.reshape(-1, 1)).flatten()

        # 5. 결과 반영
        processed_df[col] = series

    # 숫자형 데이터만 선택
    numeric_data = processed_df.select_dtypes(include=[float, int])

    # 사용자 선택 UI (멀티셀렉트로 변경)
    selected_columns = st.multiselect("시계열 그래프로 확인할 항목을 선택하세요:", numeric_data.columns, default=numeric_data.columns[:1])

    if selected_columns:
        fig, ax = plt.subplots(figsize=(12, 5))
        for col in selected_columns:
            ax.plot(processed_df.index, numeric_data[col], label=col)
        ax.set_title("Selected Time Series")
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.info("📌 하나 이상의 항목을 선택해주세요.")

    # Prophet 예측 및 성능 평가
    site_codes = ['JW', 'STI', 'SS', 'TA', 'MK', 'JM', 'YY']
    forecast_period = 48
    results = []

    for code in site_codes:
        col_name = f'{code}_Tank_Flow'
        if col_name not in processed_df.columns:
            continue

        df_prophet = processed_df[[col_name]].copy()
        df_prophet['ds'] = processed_df.index
        df_prophet.rename(columns={col_name: 'y'}, inplace=True)
        df_prophet = df_prophet[['ds', 'y']]

        model = Prophet()
        model.fit(df_prophet)

        future = model.make_future_dataframe(periods=forecast_period, freq='H')
        forecast = model.predict(future)

        merged = pd.merge(forecast[['ds', 'yhat']], df_prophet[['ds', 'y']], on='ds', how='inner')

        mae = mean_absolute_error(merged['y'], merged['yhat'])
        mse = mean_squared_error(merged['y'], merged['yhat'])
        rmse = np.sqrt(mse)
        r2 = r2_score(merged['y'], merged['yhat'])
        mape = np.mean(np.abs((merged['y'] - merged['yhat']) / merged['y'].replace(0, np.nan))) * 100

        results.append({
            '배수지': code,
            'MAE': round(mae, 3),
            'MSE': round(mse, 3),
            'RMSE': round(rmse, 3),
            'MAPE(%)': round(mape, 2),
            'R²': round(r2, 3)
        })

    performance_df = pd.DataFrame(results)
    st.subheader("📊 Prophet 기반 배수지별 예측 성능 요약")
    st.dataframe(performance_df)

    # 예측 그래프 시각화
    n_cols = 2
    n_rows = math.ceil(len(site_codes) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 7, n_rows * 4))
    axes = axes.flatten()

    for i, code in enumerate(site_codes):
        col_name = f'{code}_Tank_Flow'
        if col_name not in processed_df.columns:
            continue

        df_prophet = processed_df[[col_name]].copy()
        df_prophet['ds'] = processed_df.index
        df_prophet.rename(columns={col_name: 'y'}, inplace=True)
        df_prophet = df_prophet[['ds', 'y']]

        model = Prophet()
        model.fit(df_prophet)
        future = model.make_future_dataframe(periods=forecast_period, freq='H')
        forecast = model.predict(future)

        axes[i].plot(df_prophet['ds'], df_prophet['y'], label='Actual', color='blue')
        axes[i].plot(forecast['ds'], forecast['yhat'], label='Forecast', color='orange')
        axes[i].fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color='orange', alpha=0.2)
        axes[i].set_title(f'{code}_Tank_Flow Forecast vs Actual')
        axes[i].set_xlabel('Date')
        axes[i].set_ylabel('Flow')
        axes[i].legend()

    for j in range(len(site_codes), len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    st.pyplot(fig)



except ModuleNotFoundError as me:
    st.error("❌ 필수 라이브러리가 설치되어 있지 않습니다. requirements.txt 또는 pip install 로 누락된 패키지를 설치하세요.")
    st.code(str(me))
except Exception as e:
    st.error("❌ 파일을 불러오는 도중 오류 발생: " + str(e))
