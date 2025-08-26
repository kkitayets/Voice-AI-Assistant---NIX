import os
import sys
import time
import json
import logging
import platform
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Any
import cv2
# Настройка логирования
def setup_logging(log_level: str = "INFO", log_file: str = "vision_robot.log"):
    """Настройка системы логирования"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


# Функции для работы с файлами
def ensure_directory_exists(directory: str) -> bool:
    """Убедиться, что директория существует"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Ошибка создания директории {directory}: {e}")
        return False


def save_json(data: Any, filepath: str) -> bool:
    """Сохранить данные в JSON файл"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения JSON {filepath}: {e}")
        return False


def load_json(filepath: str) -> Optional[Any]:
    """Загрузить данные из JSON файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки JSON {filepath}: {e}")
        return None


# Функции для работы с системой
def get_system_info() -> Dict[str, Any]:
    """Получить информацию о системе"""
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "current_time": datetime.now().isoformat()
    }


def check_command_exists(command: str) -> bool:
    """Проверить, существует ли команда в системе"""
    try:
        result = subprocess.run(
            ['which', command] if platform.system() != 'Windows' else ['where', command],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def run_command(command: List[str], timeout: int = 30) -> tuple:
    """Запустить команду и вернуть результат"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


# Функции для работы с речью
def get_speech_command(text: str) -> List[str]:
    """Получить команду для синтеза речи в зависимости от ОС"""
    system = platform.system()

    if system == "Darwin":  # macOS
        return ["say", text]
    elif system == "Windows":
        return [
            "powershell",
            "-Command",
            f"Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak('{text}')"
        ]
    elif system == "Linux":
        return ["espeak", "-s", "180", text]
    else:
        return ["echo", text]  # Fallback


def speak_text(text: str) -> bool:
    """Произнести текст"""
    try:
        command = get_speech_command(text)
        result = subprocess.run(command, check=True, capture_output=True)
        logging.info(f"Произнесен текст: {text}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка синтеза речи: {e}")
        return False
    except Exception as e:
        logging.error(f"Неожиданная ошибка синтеза речи: {e}")
        return False


# Функции для работы с временем
def get_timestamp() -> str:
    """Получить текущий timestamp"""
    return datetime.now().isoformat()


def format_duration(seconds: float) -> str:
    """Форматировать длительность в читаемый вид"""
    if seconds < 60:
        return f"{seconds:.1f} сек"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} мин"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} ч"


def is_timeout(start_time: float, timeout: float) -> bool:
    """Проверить, истек ли таймаут"""
    return time.time() - start_time > timeout


# Функции для работы с текстом
def clean_text(text: str) -> str:
    """Очистить текст от лишних символов"""
    return text.strip().replace('\n', ' ').replace('\r', ' ')


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезать текст до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def contains_any_word(text: str, words: List[str]) -> bool:
    """Проверить, содержит ли текст любое из слов"""
    text_lower = text.lower()
    return any(word.lower() in text_lower for word in words)


# Функции для работы с камерой
def get_camera_info() -> Dict[str, Any]:
    """Получить информацию о доступных камерах"""
    import cv2

    cameras = []
    for i in range(5):  # Проверяем первые 5 камер
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                height, width = frame.shape[:2]
                cameras.append({
                    "index": i,
                    "width": width,
                    "height": height,
                    "fps": cap.get(cv2.CAP_PROP_FPS)
                })
            cap.release()


# utils.py - добавленные функции

def capture_frame(camera_index=0):
    """Захватить кадр с камеры"""
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    return frame


def detect_objects(frame, model_path="yolov8n.pt", confidence=0.5):
    """Обнаружение объектов на изображении с помощью YOLO"""
    try:
        from ultralytics import YOLO
        model = YOLO(model_path)
        results = model(frame, conf=confidence)

        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]

                detections.append({
                    'class': cls_name,
                    'confidence': conf,
                    'bbox': [x1, y1, x2, y2]
                })

        return detections
    except Exception as e:
        logging.error(f"Object detection error: {e}")
        return []


def format_detection_results(detections, max_objects=5):
    """Форматирование результатов обнаружения в текстовый вид"""
    if not detections:
        return "Не удалось распознать объекты"

    # Группируем объекты по классам
    object_counts = {}
    for obj in detections:
        class_name = obj['class']
        object_counts[class_name] = object_counts.get(class_name, 0) + 1

    # Формируем описание
    descriptions = []
    for class_name, count in object_counts.items():
        if count == 1:
            descriptions.append(f"{class_name}")
        else:
            descriptions.append(f"{count} {class_name}")

    return f"Я вижу: {', '.join(descriptions[:max_objects])}"


def draw_detections(frame, detections):
    """Отрисовать обнаруженные объекты на изображении"""
    for obj in detections:
        x1, y1, x2, y2 = obj['bbox']
        class_name = obj['class']
        confidence = obj['confidence']

        # Рисуем прямоугольник
        color = (0, 255, 0)  # Зеленый
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Подпись с классом и уверенностью
        label = f"{class_name} {confidence:.2f}"
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return frame