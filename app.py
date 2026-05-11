# app.py
# Интерактивное Streamlit-приложение для анализа исторических метеоданных

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# Настройки страницы
# -----------------------------
st.set_page_config(
    page_title="Анализ метеоданных",
    layout="wide"
)

st.title("🌦 Анализ и визуализация исторических метеоданных")

# -----------------------------
# Загрузка данных
# -----------------------------
st.sidebar.header("📂 Загрузка данных")

uploaded_file = st.sidebar.file_uploader(
    "Загрузите CSV-файл",
    type=["csv"]
)

# Пример структуры данных
example_data = pd.DataFrame({
    "date": pd.date_range(start="2024-01-01", periods=30),
    "city": np.random.choice(["Москва", "Рига", "Берлин"], 30),
    "temperature": np.random.randint(-10, 35, 30),
    "precipitation": np.random.uniform(0, 30, 30),
    "wind_speed": np.random.uniform(0, 20, 30)
})

# Если файл не загружен — используем пример
if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    st.warning("Используются демонстрационные данные.")
    df = example_data.copy()

# -----------------------------
# Подготовка данных
# -----------------------------
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"])

# -----------------------------
# Производные признаки
# -----------------------------
def temp_category(temp):
    if temp < 0:
        return "Холодно"
    elif temp < 20:
        return "Умеренно"
    return "Жарко"

def precipitation_level(p):
    if p == 0:
        return "Без осадков"
    elif p < 10:
        return "Небольшие"
    return "Сильные"

def comfort_level(temp, wind):
    if 18 <= temp <= 25 and wind < 10:
        return "Комфортно"
    return "Некомфортно"

df["temp_category"] = df["temperature"].apply(temp_category)
df["precipitation_level"] = df["precipitation"].apply(precipitation_level)
df["comfort"] = df.apply(
    lambda row: comfort_level(row["temperature"], row["wind_speed"]),
    axis=1
)

# -----------------------------
# Фильтры
# -----------------------------
st.sidebar.header("🔍 Фильтры")

cities = st.sidebar.multiselect(
    "Выберите города",
    options=df["city"].unique(),
    default=df["city"].unique()
)

filtered_df = df[df["city"].isin(cities)]

# Фильтр по датам
if "date" in filtered_df.columns:
    min_date = filtered_df["date"].min()
    max_date = filtered_df["date"].max()

    date_range = st.sidebar.date_input(
        "Выберите диапазон дат",
        [min_date, max_date]
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["date"] >= pd.to_datetime(start_date)) &
            (filtered_df["date"] <= pd.to_datetime(end_date))
        ]

# -----------------------------
# Таблица данных
# -----------------------------
st.header("📋 Исходные данные")

st.dataframe(
    filtered_df.sort_values(by="date"),
    use_container_width=True
)

# -----------------------------
# Основные метрики
# -----------------------------
st.header("📊 Основные показатели")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Средняя температура",
    f"{filtered_df['temperature'].mean():.1f} °C"
)

col2.metric(
    "Средние осадки",
    f"{filtered_df['precipitation'].mean():.1f} мм"
)

col3.metric(
    "Средняя скорость ветра",
    f"{filtered_df['wind_speed'].mean():.1f} м/с"
)

# -----------------------------
# EDA — распределения
# -----------------------------
st.header("📈 Разведочный анализ данных")

metric = st.selectbox(
    "Выберите показатель",
    ["temperature", "precipitation", "wind_speed"]
)

chart_type = st.radio(
    "Тип графика",
    ["Гистограмма", "Boxplot"]
)

if chart_type == "Гистограмма":
    fig = px.histogram(
        filtered_df,
        x=metric,
        color="city",
        barmode="overlay",
        nbins=20,
        title=f"Распределение {metric}"
    )
else:
    fig = px.box(
        filtered_df,
        x="city",
        y=metric,
        color="city",
        title=f"Boxplot для {metric}"
    )

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Сравнение городов
# -----------------------------
st.header("🏙 Сравнение городов")

city_stats = (
    filtered_df.groupby("city")[[
        "temperature",
        "precipitation",
        "wind_speed"
    ]]
    .mean()
    .reset_index()
)

compare_metric = st.selectbox(
    "Метрика для сравнения",
    ["temperature", "precipitation", "wind_speed"],
    key="compare_metric"
)

fig_compare = px.bar(
    city_stats,
    x="city",
    y=compare_metric,
    color="city",
    title=f"Среднее значение {compare_metric} по городам"
)

st.plotly_chart(fig_compare, use_container_width=True)

# -----------------------------
# Временной ряд
# -----------------------------
if "date" in filtered_df.columns:

    st.header("📅 Временной ряд")

    ts_metric = st.selectbox(
        "Показатель временного ряда",
        ["temperature", "precipitation", "wind_speed"],
        key="ts_metric"
    )

    city_for_ts = st.selectbox(
        "Город для анализа",
        filtered_df["city"].unique()
    )

    ts_df = filtered_df[
        filtered_df["city"] == city_for_ts
    ].sort_values("date")

    # Скользящее среднее
    ts_df["rolling_mean"] = (
        ts_df[ts_metric]
        .rolling(window=7)
        .mean()
    )

    fig_ts = go.Figure()

    fig_ts.add_trace(
        go.Scatter(
            x=ts_df["date"],
            y=ts_df[ts_metric],
            mode="lines+markers",
            name="Реальные данные"
        )
    )

    fig_ts.add_trace(
        go.Scatter(
            x=ts_df["date"],
            y=ts_df["rolling_mean"],
            mode="lines",
            name="Скользящее среднее (7 дней)"
        )
    )

    fig_ts.update_layout(
        title=f"Динамика {ts_metric} — {city_for_ts}",
        xaxis_title="Дата",
        yaxis_title=ts_metric
    )

    st.plotly_chart(fig_ts, use_container_width=True)

# -----------------------------
# Категориальные признаки
# -----------------------------
st.header("🧩 Анализ категорий")

cat_col1, cat_col2 = st.columns(2)

with cat_col1:
    fig_temp_cat = px.pie(
        filtered_df,
        names="temp_category",
        title="Категории температуры"
    )
    st.plotly_chart(fig_temp_cat, use_container_width=True)

with cat_col2:
    fig_prec = px.pie(
        filtered_df,
        names="precipitation_level",
        title="Уровни осадков"
    )
    st.plotly_chart(fig_prec, use_container_width=True)

# -----------------------------
# Выгрузка данных
# -----------------------------
st.header("💾 Скачать данные")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Скачать CSV",
    data=csv,
    file_name="filtered_weather_data.csv",
    mime="text/csv"
)

st.success("Приложение готово к использованию 🚀")