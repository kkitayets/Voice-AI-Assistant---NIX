import sys
import math
import numpy as np
import pyaudio
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath, QBrush
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QPropertyAnimation
import logging  # Добавляем импорт logging

# Импортируем функции из основного кода
from NIX_main import get_recognized_text, get_ai_response  # Замените на правильное имя файла

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

class AudioVisualizerWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_waves = 5  # Увеличиваем количество волн
        self.waves = [{'angle': 0, 'base_amplitude': 10 + i * 5} for i in range(self.num_waves)]
        self.num_points = 150
        self.colors = [QColor(93, 109, 126, 60),  # Нейтральные цвета с полупрозрачностью
                       QColor(126, 109, 93, 60),
                       QColor(109, 93, 126, 60),
                       QColor(93, 126, 109, 60),
                       QColor(126, 93, 109, 60)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_visualization)
        self.timer.start(25)
        self.setMinimumSize(400, 400)

        # Настройка аудио
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=44100,
                                  input=True,
                                  frames_per_buffer=1024)

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Центр и радиус основного круга
            rect = self.rect()
            center = QPointF(rect.width() / 2, rect.height() / 2)
            radius = min(rect.width(), rect.height()) / 4

            # Рисуем основной круг
            painter.setBrush(QColor(44, 62, 80))  # Тёмно-синий цвет
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)

            # Рисуем волны
            for index, wave in enumerate(self.waves):
                path = QPainterPath()
                for i in range(self.num_points):
                    angle = 2 * math.pi * i / self.num_points + wave['angle']
                    dynamic_wave_amplitude = wave['base_amplitude'] * (1 + 0.3 * math.sin(angle * 3 + wave['angle']))
                    wave_radius = radius + dynamic_wave_amplitude * math.sin(angle + wave['angle'])
                    x = center.x() + wave_radius * math.cos(angle)
                    y = center.y() + wave_radius * math.sin(angle)
                    if i == 0:
                        path.moveTo(x, y)
                    else:
                        path.lineTo(x, y)
                path.closeSubpath()

                # Заливаем волну полупрозрачным цветом
                painter.setBrush(QBrush(self.colors[index % len(self.colors)]))
                painter.drawPath(path)

            # Рисуем текст "NIX" поверх всех волн
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 32, QFont.Bold))
            painter.drawText(QRectF(center.x() - radius, center.y() - 25, 2 * radius, 50), Qt.AlignCenter, "NIX")
        except Exception as e:
            logging.error(f"Error in paintEvent: {e}")

    def update_visualization(self):
        try:
            # Захватываем аудиоданные
            data = np.frombuffer(self.stream.read(1024, exception_on_overflow=False), dtype=np.int16)
            peak = np.abs(data).mean() / 32768.0

            for wave in self.waves:
                wave['angle'] += 0.05 + 0.02 * (self.waves.index(wave))  # Каждая волна движется с разной скоростью
                wave['base_amplitude'] = 15 + peak * 30  # Реакция на звук, более явный отклик

            self.update()
        except Exception as e:
            logging.error(f"Error in update_visualization: {e}")

    def closeEvent(self, event):
        try:
            logging.info("Closing application")
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
            event.accept()
        except Exception as e:
            logging.error(f"Error in closeEvent: {e}")
            event.ignore()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NIX Voice Assistant")
        self.setGeometry(100, 100, 400, 400)

        # Создаем основной виджет и layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Создаем виджет визуализации
        self.visualizer = AudioVisualizerWidget(self)
        self.layout.addWidget(self.visualizer)

        # Создаем виджеты для отображения текста
        self.recognized_text_label = QLabel(self)
        self.recognized_text_label.setStyleSheet("color: white; font-size: 18px;")
        self.recognized_text_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.layout.addWidget(self.recognized_text_label)

        self.ai_response_label = QLabel(self)
        self.ai_response_label.setStyleSheet("color: white; font-size: 18px;")
        self.ai_response_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.layout.addWidget(self.ai_response_label)

        # Таймер для обновления текста
        self.text_timer = QTimer(self)
        self.text_timer.timeout.connect(self.update_text)
        self.text_timer.start(1000)  # Обновляем каждую секунду

    def update_text(self):
        try:
            recognized_text = get_recognized_text()
            ai_response = get_ai_response()

            if recognized_text is None:
                logging.info("No recognized text available.")
            else:
                logging.info(f"Recognized Text: {recognized_text}")

            if ai_response is None:
                logging.info("No AI response available.")
            else:
                logging.info(f"AI Response: {ai_response}")

            recognized_text = recognized_text or ""
            ai_response = ai_response or ""

            self.set_text_with_animation(self.recognized_text_label, recognized_text)
            self.set_text_with_animation(self.ai_response_label, ai_response)
        except Exception as e:
            logging.error(f"Error in update_text: {e}")

    def set_text_with_animation(self, label, text):
        try:
            if not text:
                label.clear()  # Очищаем текст если он пустой
            else:
                label.setText(text)  # Прямая установка текста без анимации
        except Exception as e:
            logging.error(f"Error in set_text_with_animation: {e}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()