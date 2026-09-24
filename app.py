import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import tempfile
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import av

st.set_page_config(page_title="BioSimCore Clinical Pro", layout="wide")

st.title("BioSimCore Clinical Pro: Биомеханический аудит")
st.markdown("Инструмент для автоматического трекинга суставов, расчета углов и мышечных усилий.")

# Выбор режима работы в сайдбаре
st.sidebar.header("Источник видео")
mode = st.sidebar.radio("Выберите режим:", ["📁 Загрузить видеофайл", "🔴 Веб-камера (Реальное время)"])

# Функция расчета угла между тремя точками
def calculate_angle(a, b, c):
    a = np.array(a) # Бедро
    b = np.array(b) # Колено (сустав)
    c = np.array(c) # Голеностоп
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360.0 - angle
        
    return angle

# Класс для обработки видеопотока с веб-камеры через webrtc
class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image = frame.to_ndarray(format="bgr24")
        
        # Конвертация в RGB для MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        
        image_rgb.flags.writeable = True
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, _ = image.shape
            
            # Правая нога
            hip = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x * w,
                   landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y * h]
            knee = [landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].x * w,
                    landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].y * h]
            ankle = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].x * w,
                     landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].y * h]
            
            angle = calculate_angle(hip, knee, ankle)
            
            # Расчет усилия квадрицепса
            quad_force_n = int(max(0, (180 - angle) * 25 + 400))
            quad_force_kg = int(quad_force_n / 9.81)
            
            # Отрисовка скелета
            self.mp_drawing.draw_landmarks(
                image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # Вывод текста на кадр
            cv2.putText(image, f"Knee Angle: {int(angle)} deg", 
                        (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f"Quad Force: {quad_force_n} N ({quad_force_kg} kg)", 
                        (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2, cv2.LINE_AA)
            
        return av.VideoFrame.from_ndarray(image, format="bgr24")


if mode == "📁 Загрузить видеофайл":
    uploaded_file = st.sidebar.file_uploader("Загрузить видео сеанса (MP4, AVI)", type=["mp4", "avi", "mov"])
    
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        
        cap = cv2.VideoCapture(tfile.name)
        st.success("Видео успешно загружено! Обработка...")
        
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        mp_drawing = mp.solutions.drawing_utils

        stframe = st.empty()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                h, w, _ = image.shape
                hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * w,
                       landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * h]
                knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x * w,
                        landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y * h]
                ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x * w,
                         landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y * h]
                
                angle = calculate_angle(hip, knee, ankle)
                quad_force_n = int(max(0, (180 - angle) * 25 + 400))
                quad_force_kg = int(quad_force_n / 9.81)
                
                mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                cv2.putText(image, f"Knee Angle: {int(angle)} deg", 
                            (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(image, f"Quad Force: {quad_force_n} N ({quad_force_kg} kg)", 
                            (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2, cv2.LINE_AA)
                
            stframe.image(image, channels="BGR", use_container_width=True)
            
        cap.release()
    else:
        st.info("Пожалуйста, загрузите видеофайл через боковую панель слева.")

else:
    st.subheader("Прямая трансляция с веб-камеры")
    st.markdown("Нажмите кнопку **START**, чтобы запустить обработку движений в реальном времени.")
    
    webrtc_streamer(
        key="biomech-stream",
        video_processor_factory=VideoProcessor,
        rtc_configuration=RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        ),
        media_stream_constraints={"video": True, "audio": False}
    )