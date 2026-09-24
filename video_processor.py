import cv2
import mediapipe as mp
import numpy as np
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

# Путь к вашему видеофайлу (или оставьте '' для теста, но нужен файл)
video_path = "test_movement.mp4" 
cap = cv2.VideoCapture(video_path)

# Открываем CSV-файл для записи логов симуляции
csv_file = open("simulation_log.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Frame", "Knee_Angle_Deg", "Quad_Force_N"])

frame_id = 0
print(f"Обработка видеофайла: {video_path}")

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Конец видеофайла или ошибка чтения.")
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        h, w, _ = image.shape

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * w,
                       landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * h]
                knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x * w,
                        landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y * h]
                ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x * w,
                         landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y * h]

                knee_angle = calculate_angle(hip, knee, ankle)
                
                # Модель Хилла
                base_force = 2000.0
                length_factor = max(0.2, 1.0 - abs(knee_angle - 160.0) / 100.0)
                quad_force = base_force * 0.8 * length_factor

                # Записываем данные в CSV
                csv_writer.writerow([frame_id, round(knee_angle, 2), round(quad_force, 2)])
                
                # Отрисовка текста поверх кадра
                cv2.putText(image, f"Frame: {frame_id} | Angle: {int(knee_angle)} deg", (30, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.putText(image, f"Quad Force: {int(quad_force)} N", (30, 80), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)

            except Exception as e:
                pass

        cv2.imshow('BioSimCore Video Processing', image)
        frame_id += 1

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

cap.release()
csv_file.close()
cv2.destroyAllWindows()
print("Обработка завершена. Данные сохранены в simulation_log.csv")