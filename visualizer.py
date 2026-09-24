import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

log_file = 'simulation_log.csv'

# Проверяем наличие данных, если файл пуст — генерируем демо-данные для наглядности
try:
    df = pd.read_csv(log_file)
    if len(df) == 0:
        raise ValueError("Файл пуст")
except (FileNotFoundError, ValueError):
    print("Создаем демонстрационные данные симуляции для построения графиков...")
    frames = np.arange(0, 100)
    angles = 160.0 - 40.0 * np.sin(frames / 10.0) # Симуляция приседа
    forces = 2000.0 * 0.8 * (1.0 - np.abs(angles - 160.0) / 100.0)
    df = pd.DataFrame({'Frame': frames, 'Knee_Angle_Deg': angles, 'Quad_Force_N': forces})

# Создаем графики
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 1. График угла в коленном суставе
ax1.plot(df['Frame'], df['Knee_Angle_Deg'], label='Knee Flexion Angle (°)', color='blue', linewidth=2)
ax1.set_ylabel('Angle (degrees)', fontsize=11)
ax1.set_title('BioSimCore Video Analysis: Joint Kinematics & Muscle Dynamics', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.7)

# 2. График мышечного усилия квадрицепса (Модель Хилла)
ax2.plot(df['Frame'], df['Quad_Force_N'], label='Quadriceps Force (N)', color='red', linewidth=2)
ax2.set_ylabel('Force (N)', fontsize=11)
ax2.set_xlabel('Video Frame ID', fontsize=11)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig('video_biomechanics_report.png', dpi=300)
print("График успешно сохранен как 'video_biomechanics_report.png'!")
plt.show()