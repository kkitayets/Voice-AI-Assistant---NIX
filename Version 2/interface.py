import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QSplitter, QPushButton, QTextEdit, QMessageBox)
from PyQt5.QtGui import (QPainter, QColor, QFont, QPixmap, QImage,QLinearGradient, QPen, QBrush)
from PyQt5.QtCore import (Qt, QTimer, QThread, pyqtSignal, QSize)
import logging
from datetime import datetime
import threading
from main import (get_last_user_input, get_last_ai_response,get_conversation_history, is_running,process_user_input, vision_processor)

logging.basicConfig(level=logging.INFO)
class CameraWidget(QLabel):
    """Виджет для отображения видео с камеры"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 360)
        self.setMaximumSize(640, 480)
        self.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #00d4aa;
                border-radius: 15px;
                padding: 5px;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setText("Камера инициализируется...")
        self.setWordWrap(True)

        # Таймер для обновления видео
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
        self.timer.start(50)

    def update_camera(self):
        """Обновление изображения с камеры"""
        try:
            from main import vision_processor
            frame = vision_processor.get_current_frame()

            if frame is not None:
                # Преобразуем BGR в RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Получаем размеры виджета
                widget_width = self.width()
                widget_height = self.height()

                # Масштабируем изображение
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)

                # Масштабируем с сохранением пропорций
                scaled_pixmap = pixmap.scaled(
                    widget_width, widget_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                self.setPixmap(scaled_pixmap)
            else:
                self.setText("Ожидание сигнала с камеры...")

        except Exception as e:
            logging.error(f"Camera widget error: {e}")
            self.setText("Ошибка камеры")


class ChatMessage(QFrame):
    """Виджет для одного сообщения в чате"""

    def __init__(self, message, is_user=True, timestamp=None, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(600)

        # Настройка стиля в зависимости от типа сообщения
        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 123, 255, 30);
                    border: 1px solid rgba(0, 123, 255, 50);
                    border-radius: 15px;
                    padding: 10px;
                    margin: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 212, 170, 30);
                    border: 1px solid rgba(0, 212, 170, 50);
                    border-radius: 15px;
                    padding: 10px;
                    margin: 5px;
                }
            """)

        layout = QVBoxLayout()

        # Заголовок сообщения
        header = QLabel("👤 Вы:" if is_user else "🤖 ВИЖН:")
        header.setStyleSheet("""
            QLabel {
                color: #00d4aa;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 5px;
                background: transparent;
                border: none;
                padding: 0;
            }
        """)

        # Текст сообщения
        text_label = QLabel(message)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                line-height: 1.4;
                background: transparent;
                border: none;
                padding: 0;
            }
        """)

        # Время сообщения
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = datetime.now().strftime("%H:%M:%S")
        else:
            time_str = datetime.now().strftime("%H:%M:%S")

        time_label = QLabel(time_str)
        time_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 100);
                font-size: 10px;
                background: transparent;
                border: none;
                padding: 0;
                margin-top: 5px;
            }
        """)
        time_label.setAlignment(Qt.AlignRight)

        layout.addWidget(header)
        layout.addWidget(text_label)
        layout.addWidget(time_label)

        self.setLayout(layout)


class ChatWidget(QWidget):
    """Виджет чата"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self.last_conversation_length = 0

        # Основной layout
        layout = QVBoxLayout()

        # Заголовок чата
        header = QLabel("💬 Диалог с роботом ВИЖН")
        header.setStyleSheet("""
            QLabel {
                color: #00d4aa;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                background: rgba(0, 212, 170, 20);
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)

        layout.addWidget(header)

        # Область прокрутки для сообщений
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 20);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 212, 170, 100);
                border-radius: 4px;
            }
        """)

        # Виджет для сообщений
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setSpacing(5)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)

        # Панель ввода текста
        input_layout = QHBoxLayout()

        # Поле ввода текста
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(80)
        self.text_input.setPlaceholderText("Введите сообщение для ВИЖН...")
        self.text_input.setStyleSheet("""
            QTextEdit {
                background: rgba(40, 45, 55, 150);
                border: 2px solid rgba(0, 212, 170, 50);
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 2px solid #00d4aa;
            }
        """)
        # Обработка нажатия Enter
        self.text_input.keyPressEvent = self.handle_key_press

        self.send_button = QPushButton("Отправить")
        self.send_button.setStyleSheet("""
            QPushButton {
                background: rgba(0, 212, 170, 100);
                border: none;
                border-radius: 10px;
                padding: 15px 25px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(0, 212, 170, 150);
            }
            QPushButton:pressed {
                background: rgba(0, 212, 170, 200);
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.text_input)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Статус
        self.status_label = QLabel("Ожидаю активации...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 150);
                font-size: 12px;
                font-style: italic;
                padding: 5px;
                background: rgba(0, 0, 0, 50);
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Таймер для обновления чата
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chat)
        self.timer.start(500)  # Обновляем каждые 0.5 секунды

    def handle_key_press(self, event):
        """Обработка нажатия клавиш"""
        if event.key() == Qt.Key_Return and not event.modifiers():
            # Отправляем сообщение при нажатии Enter без Shift
            self.send_message()
            event.accept()
        elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
            # Вставляем новую строку при Shift+Enter
            self.text_input.insertPlainText("\n")
            event.accept()
        else:
            # Стандартная обработка
            super().keyPressEvent(event)

    def send_message(self):
        """Отправить сообщение"""
        text = self.text_input.toPlainText().strip()
        if text:
            # Отправляем сообщение в отдельном потоке
            threading.Thread(target=self.process_message, args=(text,), daemon=True).start()
            self.text_input.clear()

    def process_message(self, text):
        """Обработать сообщение"""
        try:
            process_user_input(text)
        except Exception as e:
            logging.error(f"Message processing error: {e}")

    def add_message(self, message, is_user=True, timestamp=None):
        """Добавить сообщение в чат"""
        chat_message = ChatMessage(message, is_user, timestamp)

        # Добавляем перед stretch
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, chat_message)

        # Прокручиваем вниз
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Прокрутить чат вниз"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_chat(self):
        """Обновление чата"""
        try:
            conversation = get_conversation_history()

            # Проверяем, есть ли новые сообщения
            if len(conversation) > self.last_conversation_length:
                # Добавляем новые сообщения
                for msg in conversation[self.last_conversation_length:]:
                    is_user = msg['role'] == 'user'
                    timestamp = msg.get('timestamp')
                    self.add_message(msg['content'], is_user, timestamp)

                self.last_conversation_length = len(conversation)

            # Обновляем статус
            if is_running():
                last_user = get_last_user_input()
                last_ai = get_last_ai_response()

                if last_user:
                    self.status_label.setText("🎤 Обрабатываю...")
                elif last_ai:
                    self.status_label.setText("🤖 Отвечаю...")
                else:
                    self.status_label.setText("💤 Ожидаю...")
            else:
                self.status_label.setText("❌ Не активен")

        except Exception as e:
            logging.error(f"Chat update error: {e}")


class StatusWidget(QWidget):
    """Виджет статуса системы"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self.setStyleSheet("""
            QWidget {
                background: rgba(20, 25, 35, 200);
                border: 1px solid rgba(0, 212, 170, 50);
                border-radius: 15px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("🔍 Статус системы ВИЖН")
        title.setStyleSheet("""
            QLabel {
                color: #00d4aa;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)

        # Индикаторы статуса
        self.camera_status = QLabel("📹 Камера: Инициализация")
        self.ai_status = QLabel("🧠 ИИ: Готов")
        self.speech_status = QLabel("🎤 Речь: Ожидание")

        status_style = """
            QLabel {
                color: white;
                font-size: 12px;
                padding: 2px 5px;
                background: rgba(0, 0, 0, 30);
                border-radius: 5px;
                margin: 2px;
            }
        """

        self.camera_status.setStyleSheet(status_style)
        self.ai_status.setStyleSheet(status_style)
        self.speech_status.setStyleSheet(status_style)

        layout.addWidget(title)
        layout.addWidget(self.camera_status)
        layout.addWidget(self.ai_status)
        layout.addWidget(self.speech_status)

        self.setLayout(layout)

        # Таймер для обновления статуса
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # Обновляем каждую секунду

    def update_status(self):
        """Обновление статуса"""
        try:
            # Статус камеры
            if vision_processor.running and vision_processor.get_current_frame() is not None:
                self.camera_status.setText("📹 Камера: ✅ Активна")
            else:
                self.camera_status.setText("📹 Камера: ❌ Нет сигнала")

            # Статус ИИ
            if is_running():
                self.ai_status.setText("🧠 ИИ: ✅ Готов")
            else:
                self.ai_status.setText("🧠 ИИ: ❌ Не активен")

            # Статус речи
            last_input = get_last_user_input()
            if last_input:
                self.speech_status.setText(f"🎤 Речь: 📝 {last_input[:30]}...")
            else:
                self.speech_status.setText("🎤 Речь: 👂 Слушаю...")

        except Exception as e:
            logging.error(f"Status update error: {e}")


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VISION Robot Interface")
        self.setGeometry(100, 100, 1400, 900)

        # Основной виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Темная тема
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #0f1419, stop:0.5 #1a1f29, stop:1 #0a0f14);
            }
            QWidget {
                background: transparent;
                color: white;
            }
        """)

        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Левая панель (камера и статус)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)

        # Заголовок камеры
        camera_title = QLabel("📹 Камера робота ВИЖН")
        camera_title.setStyleSheet("""
            QLabel {
                color: #00d4aa;
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
                background: rgba(0, 212, 170, 20);
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        camera_title.setAlignment(Qt.AlignCenter)

        # Камера
        self.camera_widget = CameraWidget()

        # Статус
        self.status_widget = StatusWidget()

        # Кнопки управления
        control_layout = QHBoxLayout()

        self.emergency_button = QPushButton("🚨 Экстренная остановка")
        self.emergency_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 50, 50, 100);
                border: none;
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 50, 50, 150);
            }
        """)
        self.emergency_button.clicked.connect(self.emergency_stop)

        self.info_button = QPushButton("ℹ️ Информация")
        self.info_button.setStyleSheet("""
            QPushButton {
                background: rgba(100, 100, 100, 100);
                border: none;
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(100, 100, 100, 150);
            }
        """)
        self.info_button.clicked.connect(self.show_info)

        control_layout.addWidget(self.emergency_button)
        control_layout.addWidget(self.info_button)

        left_layout.addWidget(camera_title)
        left_layout.addWidget(self.camera_widget)
        left_layout.addWidget(self.status_widget)
        left_layout.addLayout(control_layout)
        left_layout.addStretch()

        # Правая панель (чат)
        self.chat_widget = ChatWidget()

        # Добавляем панели в основной layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(self.chat_widget, 2)

    def emergency_stop(self):
        """Экстренная остановка"""
        reply = QMessageBox.question(self, 'Экстренная остановка',
                                     'Вы действительно хотите остановить робота ВИЖН?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Здесь можно добавить код для остановки основного процесса
            QApplication.quit()

    def show_info(self):
        """Показать информацию о роботе"""
        info_text = """
        🤖 Робот ВИЖН v1.0

        Возможности:
        • Распознавание речи
        • Компьютерное зрение (YOLO)
        • Диалог с ИИ (DeepSeek v3)
        • Проактивные разговоры
        • Анализ окружающей среды

        Команды активации:
        • "Привет ВИЖН" - активация
        • "Что ты видишь?" - анализ изображения
        • "Пока" - завершение работы

        Разработано для интеллектуального взаимодействия
        с использованием современных технологий ИИ.
        """

        QMessageBox.information(self, 'О роботе ВИЖН', info_text)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        reply = QMessageBox.question(self, 'Закрытие приложения',
                                     'Вы действительно хотите закрыть интерфейс?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    """Главная функция запуска интерфейса"""
    app = QApplication(sys.argv)

    # Устанавливаем иконку приложения (если есть)
    app.setApplicationName("VISION Robot Interface")
    app.setApplicationVersion("1.0")

    # Создаем главное окно
    window = MainWindow()
    window.show()

    # Запускаем приложение
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

