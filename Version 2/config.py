"""
Конфигурация для VISION Robot
"""

import os
import sys
import platform

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEEPSEEK_MODEL = "deepseek/deepseek-chat"

# Camera Configuration
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# YOLO Configuration
YOLO_MODEL_PATH = "yolov8n.pt"
YOLO_CONFIDENCE_THRESHOLD = 0.5
YOLO_NMS_THRESHOLD = 0.4

# Speech Recognition Configuration
SPEECH_LANGUAGE = "ru-RU"
SPEECH_TIMEOUT = 1
SPEECH_PHRASE_TIME_LIMIT = 5

# Speech Synthesis Configuration
SPEECH_RATE = 180  # слов в минуту
SPEECH_VOLUME = 0.8

# System Configuration
SYSTEM = platform.system()
PYTHON_VERSION = sys.version_info

# Timing Configuration
PROACTIVE_CONVERSATION_TIMEOUT = 35  # секунд
CAMERA_UPDATE_INTERVAL = 0.5  # секунд
CHAT_UPDATE_INTERVAL = 0.5  # секунд
STATUS_UPDATE_INTERVAL = 1.0  # секунд

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "vision_robot.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Interface Configuration
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
WINDOW_TITLE = "VISION Robot Interface"

# Colors (для интерфейса)
COLORS = {
    "primary": "#00d4aa",
    "secondary": "#007bff",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "dark": "#343a40",
    "light": "#f8f9fa"
}

# Activation words
ACTIVATION_WORDS = [
    "привет вижн",
    "привет vision",
    "вижн привет",
    "vision привет",
    "включись",
    "проснись"
]

EXIT_WORDS = [
    "останови программу",
    "пока",
    "завершить",
    "стоп",
    "выход",
    "отключись"
]

# Vision keywords
VISION_KEYWORDS = [
    "что ты видишь",
    "что видишь",
    "что я показываю",
    "что это",
    "посмотри",
    "что на экране",
    "анализируй",
    "что перед тобой"
]

# System prompts
SYSTEM_PROMPTS = {
    "main": (
        "Ты робот ВИЖН - дружелюбный помощник с компьютерным зрением. "
        "Ты можешь видеть окружающий мир через камеру и анализировать объекты. "
        "Отвечай естественно и дружелюбно, как живой собеседник. "
        "Не упоминай, что ты ИИ. Ты просто ВИЖН - робот с камерой. "
        "Будь вежливым, полезным и интересным собеседником."
    ),
    "proactive": (
        "Ты робот ВИЖН. Инициируй дружелюбный диалог с пользователем. "
        "Будь естественным и интересным в разговоре. "
        "Можешь спросить о том, что происходит, или предложить поговорить о чем-то интересном."
    )
}

# Greetings
GREETINGS = [
    "Привет! Меня зовут ВИЖН. Я вижу мир через камеру и готов с вами поговорить!",
    "Здравствуйте! Я ВИЖН, ваш визуальный помощник. Что интересного происходит вокруг?",
    "Приветствую! Я робот ВИЖН, готов к разговору и наблюдению за окружающим миром.",
    "Добро пожаловать! Я ВИЖН - ваш умный помощник с компьютерным зрением.",
    "Привет! Я ВИЖН, и я готов помочь вам и поговорить о том, что вижу вокруг!"
]

# Proactive conversation starters
PROACTIVE_STARTERS = [
    "Кстати, а что вы сейчас делаете? Мне интересно!",
    "Я тут наблюдаю за происходящим... Хотите поболтать?",
    "А знаете, мне скучно просто смотреть. Давайте поговорим!",
    "Что-то давно вы со мной не разговариваете. Как дела?",
    "Интересно, что вы думаете о том, что происходит сейчас?",
    "Хотите, расскажу что-нибудь интересное о том, что вижу?",
    "А давайте поиграем в игру! Я буду описывать что вижу, а вы угадывать!",
    "Знаете, я заметил кое-что интересное... Хотите обсудить?",
    "Может, поговорим о чем-нибудь? Мне одиноко просто наблюдать.",
    "Кстати, у меня есть вопрос к вам! Готовы к разговору?"
]

# Goodbyes
GOODBYES = [
    "До свидания! Было приятно с вами пообщаться!",
    "Увидимся! Буду скучать по нашим разговорам.",
    "Пока! Обязательно поговорим еще!",
    "До встречи! Мне понравилось с вами общаться.",
    "Всего доброго! Жду нашей следующей беседы!",
    "Прощайте! Было здорово поболтать.",
    "До свидания! Берегите себя!",
    "Пока-пока! Скоро увидимся!"
]

# Error messages
ERROR_MESSAGES = {
    "camera_not_found": "Камера не найдена или недоступна",
    "microphone_error": "Проблема с микрофоном",
    "api_error": "Ошибка подключения к API",
    "speech_recognition_error": "Ошибка распознавания речи",
    "yolo_error": "Ошибка анализа изображения",
    "config_error": "Ошибка конфигурации"
}

# Status messages
STATUS_MESSAGES = {
    "initializing": "Инициализация...",
    "ready": "Готов к работе",
    "listening": "Слушаю...",
    "processing": "Обрабатываю...",
    "responding": "Отвечаю...",
    "error": "Ошибка",
    "offline": "Не активен"
}

# Platform-specific configurations
if SYSTEM == "Darwin":  # macOS
    SPEECH_COMMAND = "say"
    SPEECH_ARGS = ["-r", str(SPEECH_RATE)]
elif SYSTEM == "Windows":
    SPEECH_COMMAND = "powershell"
    SPEECH_ARGS = ["-Command",
                   "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak('{}')"]
elif SYSTEM == "Linux":
    SPEECH_COMMAND = "espeak"
    SPEECH_ARGS = ["-s", str(SPEECH_RATE)]


# Validate configuration
def validate_config():
    """Проверка конфигурации"""
    errors = []

    if OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY_HERE":
        errors.append("API ключ OpenRouter не установлен")

    if not os.path.exists(YOLO_MODEL_PATH):
        errors.append(f"Модель YOLO не найдена: {YOLO_MODEL_PATH}")

    if PYTHON_VERSION < (3, 7):
        errors.append("Требуется Python 3.7 или выше")

    return errors


# Get configuration summary
def get_config_summary():
    """Получить сводку конфигурации"""
    return {
        "system": SYSTEM,
        "python_version": f"{PYTHON_VERSION.major}.{PYTHON_VERSION.minor}.{PYTHON_VERSION.micro}",
        "camera_index": CAMERA_INDEX,
        "yolo_model": YOLO_MODEL_PATH,
        "speech_language": SPEECH_LANGUAGE,
        "api_configured": OPENROUTER_API_KEY != "YOUR_OPENROUTER_API_KEY_HERE"
    }