import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import tempfile

st.set_page_config(page_title="BioSimCore Clinical Pro", layout="wide")

st.title("BioSimCore Clinical Pro: Анализ движений")
st.markdown("Загрузите видеозапись сеанса для автоматического скелетного трекинга и расчета биомеханики.")

# Загрузка видеофайла пользователем
uploaded_file = st.sidebar.file_uploader("Загрузить видео сеанса (MP4, AVI)", type=["mp4", "avi", "mov"])

if uploaded_file is not None:
    # Сохраняем во временный файл для обработки OpenCV
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    
    cap = cv2.VideoCapture(tfile.name)
    
    st.sidebar.success("Видео успешно загружено в систему!")
    
    # Инициализация MediaPipe Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils

    st.subheader("Результат обработки видео в реальном времени")
    stframe = st.empty()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Конвертация цвета для MediaPipe
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        
        # Отрисовка скелета
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
        # Показываем кадр в интерфейсе Streamlit
        stframe.image(image, channels="BGR", use_container_width=True)
        
    cap.release()
else:
    st.info("Пожалуйста, загрузите видеофайл через боковую панель слева, чтобы запустить анализ.")