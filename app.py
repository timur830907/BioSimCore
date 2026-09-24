import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="BioSimCore Clinical Pro", layout="wide")

st.title("BioSimCore Clinical Pro: Веб-платформа биомеханического аудита")
st.markdown("Профессиональный анализ движений, расчет мышечных усилий по модели Хилла и контроль осанки.")

# Боковая панель управления
st.sidebar.header("Параметры сеанса")
mode = st.sidebar.selectbox("Выберите режим аудита", ["Контроль сидения", "Анализ приседаний", "Анализ походки"])
uploaded_file = st.sidebar.file_uploader("Загрузите CSV-лог или видео сеанса", type=["csv", "mp4"])

col1, col2 = st.columns(2)

with col1:
    st.subheader("Телеметрия в реальном времени")
    # Демо-метрики для интерфейса
    st.metric(label="Угол коленного сустава", value="165 °", delta="-5 ° от нормы")
    st.metric(label="Наклон торса (осанка)", value="4 °", delta="Норма")
    st.metric(label="Усилие квадрицепса ($F_m$)", value="1420 N", delta="+120 N")
    
    st.info(f"Активный медицинский профиль: **{mode}**. Статус: Все показатели в пределах нормы.")

with col2:
    st.subheader("Биомеханические графики")
    # Генерация демонстрационного графика для сайта
    frames = np.arange(0, 50)
    angles = 160.0 - 30.0 * np.sin(frames / 8.0)
    forces = 2000.0 * 0.8 * (1.0 - np.abs(angles - 160.0) / 100.0)
    
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(frames, angles, color='blue', label='Угол колена (°)')
    ax.set_ylabel('Градусы')
    ax.set_xlabel('Кадры сеанса')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper right')
    st.pyplot(fig)

st.markdown("---")
st.caption("BioSimCore Clinical Pro Engine v2.4 | Разработано для медицинского и эргономического аудита.")