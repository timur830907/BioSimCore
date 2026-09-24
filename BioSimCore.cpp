#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <fstream> // Для экспорта в CSV

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Режимы движения
enum class MovementMode {
    WALKING,
    JUMPING_PREP,
    JUMPING_FLIGHT,
    JUMPING_LANDING
};

// Превращаем перечисление в текст для логов
std::string modeToString(MovementMode mode) {
    switch (mode) {
        case MovementMode::WALKING: return "WALKING";
        case MovementMode::JUMPING_PREP: return "JUMP_PREP";
        case MovementMode::JUMPING_FLIGHT: return "FLIGHT";
        case MovementMode::JUMPING_LANDING: return "LANDING";
    }
    return "UNKNOWN";
}

struct BodySegment {
    std::string name;
    double mass;          // кг
    double length;        // м
    double angle;         // текущий угол в радианах
};

// Модель мышцы Хилла
struct HillMuscle {
    std::string name;
    double maxIsometricForce; // Максимальная сила (Н)
    double activation;        // Уровень нервной активации (0.0 до 1.0)
    double optimalLength;     // Оптимальная длина (м)

    double getForce(double externalLoadFactor) {
        double loadMultiplier = 1.0 + (externalLoadFactor * 0.05);
        return maxIsometricForce * activation * loadMultiplier;
    }
};

class BiomechEnvironment {
private:
    double gravity = 9.81;
    double externalLoad = 0.0;
    double simulationTime = 0.0;
    
    MovementMode currentMode = MovementMode::WALKING;
    std::vector<BodySegment> segments;
    std::vector<HillMuscle> muscles;
    
    std::ofstream csvFile; // Поток для записи CSV

public:
    BiomechEnvironment() {
        // Открываем файл для логирования при создании объекта
        csvFile.open("simulation_log.csv");
        if (csvFile.is_open()) {
            // Записываем заголовки столбцов CSV
            csvFile << "Time,Mode,EffectiveMass,GRF,MuscleName,MuscleForce,JointTorque\n";
        }
    }

    ~BiomechEnvironment() {
        if (csvFile.is_open()) {
            csvFile.close();
            std::cout << "\n[Export] Data successfully saved to 'simulation_log.csv'\n";
        }
    }

    void setExternalLoad(double weight) {
        externalLoad = weight;
        std::cout << "[Setup] External load set to: " << externalLoad << " kg\n";
    }

    void addSegment(std::string name, double mass, double length) {
        segments.push_back({name, mass, length, 0.0});
    }

    void addMuscle(std::string name, double maxForce, double optLength) {
        muscles.push_back({name, maxForce, 0.4, optLength});
    }

    void setMode(MovementMode mode) {
        currentMode = mode;
        std::cout << "\n=== Switching Movement Mode: " << modeToString(mode) << " ===\n";
    }

    void updateKinematics(double dt) {
        if (currentMode == MovementMode::WALKING) {
            double stepFrequency = 1.5; 
            double phase = 2.0 * M_PI * stepFrequency * simulationTime;
            segments[0].angle = 0.3 * std::sin(phase);
            segments[1].angle = -0.4 + 0.3 * std::cos(phase);
        } 
        else if (currentMode == MovementMode::JUMPING_PREP) {
            segments[0].angle = 0.6; 
            segments[1].angle = -1.1; 
            for (auto& m : muscles) m.activation = 0.95; 
        } 
        else if (currentMode == MovementMode::JUMPING_FLIGHT) {
            segments[0].angle = 0.0;
            segments[1].angle = 0.0;
            for (auto& m : muscles) m.activation = 0.05; 
        }
        else if (currentMode == MovementMode::JUMPING_LANDING) {
            segments[0].angle = 0.4;
            segments[1].angle = -0.8;
            for (auto& m : muscles) m.activation = 0.8; 
        }
    }

    void updateDynamicsAndForces() {
        double totalBodyMass = 0.0;
        for (const auto& seg : segments) {
            totalBodyMass += seg.mass;
        }
        double effectiveMass = totalBodyMass + externalLoad;
        double totalGravityForce = effectiveMass * gravity;

        double groundReactionForce = totalGravityForce;
        if (currentMode == MovementMode::JUMPING_FLIGHT) {
            groundReactionForce = 0.0;
        } 
        else if (currentMode == MovementMode::JUMPING_LANDING) {
            groundReactionForce = totalGravityForce * 2.5; 
        }

        std::cout << "  -> Effective Mass: " << effectiveMass << " kg | GRF: " << groundReactionForce << " N\n";

        // Расчет мышечных усилий и крутящих моментов в суставах (Torque = Force * LeverLength)
        for (size_t i = 0; i < muscles.size() && i < segments.size(); ++i) {
            double muscleForce = muscles[i].getForce(externalLoad);
            
            // Крутящий момент в суставе = Сила мышцы * плечо рычага (длина сегмента)
            double jointTorque = muscleForce * segments[i].length;

            std::cout << "  -> [" << muscles[i].name << "] Force: " << muscleForce 
                      << " N | Joint Torque: " << jointTorque << " Nm\n";

            // Запись шага симуляции в CSV файл
            if (csvFile.is_open()) {
                csvFile << simulationTime << ","
                        << modeToString(currentMode) << ","
                        << effectiveMass << ","
                        << groundReactionForce << ","
                        << muscles[i].name << ","
                        << muscleForce << ","
                        << jointTorque << "\n";
            }
        }
    }

    void step(double dt) {
        simulationTime += dt;
        std::cout << "\n--- Time: " << simulationTime << " s ---\n";
        updateKinematics(dt);
        updateDynamicsAndForces();
    }
};

int main() {
    std::cout << "=== Project: BioSimCore (Full Features) ===\n";

    // 1. Интерактивный ввод веса с клавиатуры
    double userLoad = 0.0;
    std::cout << "Введите дополнительный внешний вес (кг, например, 20 или 35): ";
    if (std::cin >> userLoad) {
        std::cout << "Принято! Внешний вес установлен: " << userLoad << " кг.\n";
    } else {
        userLoad = 15.0; // Значение по умолчанию при ошибке ввода
        std::cout << "Ошибка ввода. Установлен вес по умолчанию: 15 кг.\n";
    }

    BiomechEnvironment sim;
    sim.setExternalLoad(userLoad);

    // Настройка сегментов и мышц
    sim.addSegment("Thigh (Бедро)", 7.0, 0.45);
    sim.addSegment("Shin (Голень)", 3.5, 0.42);

    sim.addMuscle("Quadriceps", 3500.0, 0.4);
    sim.addMuscle("Triceps Surae", 2500.0, 0.2);

    // Запуск сценариев движения
    sim.setMode(MovementMode::WALKING);
    sim.step(0.1);

    sim.setMode(MovementMode::JUMPING_PREP);
    sim.step(0.1);

    sim.setMode(MovementMode::JUMPING_FLIGHT);
    sim.step(0.1);

    sim.setMode(MovementMode::JUMPING_LANDING);
    sim.step(0.1);

    return 0;
}