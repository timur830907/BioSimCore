import cv2
import mediapipe as mp
import numpy as np
import time
import csv

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle

cap = cv2.VideoCapture(0)
mode = "sitting"

# Буферы для фильтрации шумов (скользящее среднее)
angle_buffer = []
BUFFER_SIZE = 5

# Логгер сеанса
session_file = open("clinical_session_log.csv", mode="w", newline="", encoding="utf-8")
csv_writer = csv.writer(session_file)
csv_writer.writerow(["Timestamp", "Mode", "Knee_Angle", "Trunk_Angle", "Quad_Force_N", "Status"])

print("Запуск BioSimCore Clinical Pro. Нажмите '1'-Сидение, '2'-Присед, '3'-Ходьба, 's'-Сохранить отчет, 'q'-Выход.")

with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Зеркальное отображение для удобства
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Создаем профессиональную боковую панель для телеметрии (ширина 350px)
        panel_width = 360
        canvas = np.zeros((h, w + panel_width, 3), dtype=np.uint8)
        canvas[:, :w] = frame

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        is_correct = True
        status_message = "Норма"
        color_theme = (0, 255, 0)
        knee_angle = 180.0
        trunk_angle = 0.0
        quad_force = 0.0

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * w,
                            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y * h]
                hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * w,
                       landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * h]
                knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x * w,
                        landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y * h]
                ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x * w,
                         landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y * h]

                raw_knee_angle = calculate_angle(hip, knee, ankle)
                
                # Применяем фильтр скользящего среднего для устранения дрожания
                angle_buffer.append(raw_knee_angle)
                if len(angle_buffer) > BUFFER_SIZE:
                    angle_buffer.pop(0)
                knee_angle = np.mean(angle_buffer)

                vertical_point = [hip[0], hip[1] - 100]
                trunk_angle = calculate_angle(shoulder, hip, vertical_point)

                # Модель Хилла для расчета усилия
                base_force = 2200.0
                length_factor = max(0.2, 1.0 - abs(knee_angle - 160.0) / 100.0)
                quad_force = base_force * 0.8 * length_factor

                # Аудит по режимам
                if mode == "sitting":
                    if trunk_angle > 14:
                        is_correct = False
                        status_message = "Ошибка: Сутулость"
                    elif knee_angle < 75 or knee_angle > 115:
                        is_correct = False
                        status_message = "Ошибка: Угол ног в кресле"
                    else:
                        status_message = "Посадка в норме"
                elif mode == "squat":
                    if knee_angle < 70:
                        is_correct = False
                        status_message = "Ошибка: Перегиб колена"
                    elif trunk_angle > 30:
                        is_correct = False
                        status_message = "Ошибка: Наклон корпуса"
                    else:
                        status_message = "Техника стабильна"
                elif mode == "gait":
                    status_message = "Анализ фазы шага"

                color_theme = (0, 255, 0) if is_correct else (0, 0, 255)

            except Exception as e:
                pass

            # Рисуем скелет на видеочасти
            mp_drawing.draw_landmarks(
                canvas[:, :w], results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=color_theme, thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(255, 100, 0), thickness=2, circle_radius=2)
            )

        # Отрисовка профессиональной панели телеметрии справа
        cv2.rectangle(canvas, (w, 0), (w + panel_width, h), (30, 30, 30), -1)
        cv2.putText(canvas, "BIOSIMCORE CLINICAL", (w + 20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(canvas, f"Mode: {mode.upper()}", (w + 20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Блок метрик
        cv2.putText(canvas, "Метрики движения:", (w + 20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.putText(canvas, f"Угол колена: {int(knee_angle)} deg", (w + 20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(canvas, f"Наклон торса: {int(trunk_angle)} deg", (w + 20, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(canvas, f"Сила квадрицепса: {int(quad_force)} N", (w + 20, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)

        # Блок статуса аудита
        cv2.putText(canvas, "Клинический статус:", (w + 20, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.putText(canvas, status_message, (w + 20, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_theme, 2)

        # Подсказки по управлению внизу панели
        cv2.putText(canvas, "[1] Сидение  [2] Присед", (w + 20, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        cv2.putText(canvas, "[3] Ходьба   [q] Выход", (w + 20, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        # Логируем кадр в файл
        csv_writer.writerow([time.strftime("%H:%M:%S"), mode, round(knee_angle, 1), round(trunk_angle, 1), round(quad_force, 1), status_message])

        cv2.imshow('BioSimCore Clinical Pro Dashboard', canvas)

        key = cv2.waitKey(10) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('1'):
            mode = "sitting"
        elif key == ord('2'):
            mode = "squat"
        elif key == ord('3'):
            mode = "gait"

cap.release()
session_file.close()
cv2.destroyAllWindows()