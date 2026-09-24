import cv2
import mediapipe as mp
import numpy as np

# Инициализация MediaPipe Pose
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Функция для расчета угла между тремя точками (например, бедро-колено-лодыжка)
def calculate_angle(a, b, c):
    a = np.array(a) # Первая точка (Бедро)
    b = np.array(b) # Центральная точка (Колено)
    c = np.array(c) # Конечная точка (Лодыжка)
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360.0 - angle
        
    return angle

# Открываем веб-камеру
cap = cv2.VideoCapture(0)

print("Запуск продвинутого биомеханического анализа. Нажмите 'q' для выхода.")

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Не удалось получить кадр с веб-камеры.")
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        h, w, _ = image.shape

        if results.pose_landmarks:
            # Рисуем скелет
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
            )

            landmarks = results.pose_landmarks.landmark
            
            try:
                # Извлекаем координаты для правой ноги
                hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * w,
                       landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * h]
                knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x * w,
                        landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y * h]
                ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x * w,
                         landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y * h]

                # Вычисляем угол в колене
                knee_angle = calculate_angle(hip, knee, ankle)

                # Упрощенная биомеханическая модель Хилла:
                # Сила мышцы зависит от степени сгибания сустава (длины мышцы)
                # При разгибании (180°) и сильном сгибании (<90°) сила меняется
                base_isometric_force = 2000.0  # Ньютоны
                activation_factor = 0.8        # Уровень нервной активации
                
                # Коэффициент длины мышцы (аппроксимация параболы соотношения сила-длина)
                length_factor = max(0.2, 1.0 - abs(knee_angle - 160.0) / 100.0)
                
                # Итоговый расчет силы квадрицепса (F_m)
                quad_force = base_isometric_force * activation_factor * length_factor

                # Вывод интерфейса биомеханики
                cv2.putText(image, "BioSimCore: Active Dynamics", (30, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(image, f"Knee Angle: {int(knee_angle)} deg", (30, 80), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(image, f"Quad Force (F_m): {int(quad_force)} N", (30, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2, cv2.LINE_AA)
                
                # Рисуем круг на колене для наглядности
                cv2.circle(image, (int(knee[0]), int(knee[1])), 10, (0, 0, 255), -1)

            except Exception as e:
                pass

        cv2.imshow('Human Biomechanics Real-Time Analysis', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()