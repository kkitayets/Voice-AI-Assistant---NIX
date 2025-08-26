import os
import cv2
import time
import json
import logging
import requests
import threading
import numpy as np
import speech_recognition as sr
from multiprocessing import Process, Value, Queue
from datetime import datetime
from ultralytics import YOLO
import subprocess
import random
from config import (
    OPENROUTER_API_KEY,
    CAMERA_INDEX,
    YOLO_MODEL_PATH,
    ACTIVATION_WORDS,
    EXIT_WORDS,
    PROACTIVE_CONVERSATION_TIMEOUT
)
from vision_processor import VisionProcessor
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OpenRouter API Configuration
OPENROUTER_API_KEY = "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"  # Замените на ваш ключ
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Global variables
conversation_history = []
last_user_input = None
last_ai_response = None
running_flag = Value('b', True)
camera_active = Value('b', True)
last_activity_time = time.time()
proactive_conversation_enabled = Value('b', True)

vision_processor = VisionProcessor(
    camera_index=CAMERA_INDEX,
    model_path=YOLO_MODEL_PATH,
    update_interval=0.5
)

# Initialize YOLO model
try:
    yolo_model = YOLO('yolov8n.pt')  # Используем YOLOv8 (более современная версия)
    logging.info("YOLO model loaded successfully")
except Exception as e:
    logging.error(f"Failed to load YOLO model: {e}")
    yolo_model = None

vision_processor = VisionProcessor(
    camera_index=CAMERA_INDEX,
    model_path=YOLO_MODEL_PATH,
    update_interval=0.5
)

# Greetings and conversation starters
greetings = [
    "Привет! Меня зовут ВИЖН. Я вижу мир через камеру и готов с вами поговорить!",
    "Здравствуйте! Я ВИЖН, ваш визуальный помощник. Что интересного происходит вокруг?",
    "Приветствую! Я робот ВИЖН, готов к разговору и наблюдению за окружающим миром.",
]

proactive_starters = [
    "Кстати, а что вы сейчас делаете? Мне интересно!",
    "Я тут наблюдаю за происходящим... Хотите поболтать?",
    "А знаете, мне скучно просто смотреть. Давайте поговорим!",
    "Что-то давно вы со мной не разговариваете. Как дела?",
    "Интересно, что вы думаете о том, что происходит сейчас?",
]

goodbyes = [
    "До свидания! Было приятно с вами пообщаться!",
    "Увидимся! Буду скучать по нашим разговорам.",
    "Пока! Обязательно поговорим еще!",
]


def get_last_user_input():
    """Получить последний ввод пользователя"""
    return last_user_input


def get_last_ai_response():
    """Получить последний ответ ИИ"""
    return last_ai_response


def get_conversation_history():
    """Получить историю разговора"""
    return conversation_history.copy()


def is_running():
    """Проверить, работает ли робот"""
    return running_flag.value


def speak(text):
    """Произнести текст"""
    try:
        subprocess.run(['say', text], check=True)
        logging.info(f"Speaking: {text}")
    except Exception as e:
        logging.error(f"Speech error: {e}")


def call_deepseek_api(messages):
    """Вызов API DeepSeek через OpenRouter"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "VISION Robot"
        }

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }

        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logging.error(f"API Error: {response.status_code} - {response.text}")
            return "Извините, произошла ошибка при обработке запроса."

    except Exception as e:
        logging.error(f"DeepSeek API error: {e}")
        return "Извините, не могу подключиться к серверу."


def recognize_speech():
    """Распознавание речи"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        logging.info("Listening for speech...")
        try:
            audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language="ru-RU")
            logging.info(f"Recognized: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logging.error(f"Speech recognition error: {e}")
            return None

def get_vision_description():
    """Получить описание того, что видит робот"""
    if vision_processor.running:
        return vision_processor.get_detection_description()
    return "Система зрения не активна"

def get_last_vision_result():
    """Получить последний результат компьютерного зрения"""
    if vision_processor.running:
        return vision_processor.get_current_frame()
    return None


def camera_monitor():
    """Мониторинг камеры"""
    vision_processor.start()
    logging.info("Vision processor started")

    while running_flag.value:
        time.sleep(1)

    vision_processor.stop()
    logging.info("Vision processor stopped")


def proactive_conversation():
    """Проактивный диалог"""
    global last_activity_time, last_ai_response

    while running_flag.value:
        try:
            current_time = time.time()

            # Проверяем, прошло ли достаточно времени с последней активности
            if (proactive_conversation_enabled.value and
                    current_time - last_activity_time > 35 and  # 35 секунд
                    len(conversation_history) > 0):  # Есть история диалога

                # Запускаем проактивный диалог
                starter = random.choice(proactive_starters)
                logging.info(f"Proactive conversation: {starter}")

                # Добавляем в историю
                conversation_history.append({
                    'role': 'assistant',
                    'content': starter,
                    'timestamp': datetime.now().isoformat()
                })

                last_ai_response = starter
                speak(starter)

                # Обновляем время последней активности
                last_activity_time = current_time

            time.sleep(5)  # Проверяем каждые 5 секунд

        except Exception as e:
            logging.error(f"Proactive conversation error: {e}")
            time.sleep(10)


def process_user_input(user_input):
    """Обработка ввода пользователя"""
    global last_user_input, last_ai_response, last_activity_time

    last_user_input = user_input
    last_activity_time = time.time()

    # Добавляем пользовательский ввод в историю
    conversation_history.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().isoformat()
    })

    # Проверяем, спрашивает ли пользователь о том, что видит робот
    vision_keywords = ['что ты видишь', 'что видишь', 'что я показываю', 'что это', 'посмотри', 'что на экране']

    should_analyze_vision = any(keyword in user_input.lower() for keyword in vision_keywords)

    # Формируем сообщения для API
    messages = [
        {
            "role": "system",
            "content": (
                "Ты робот ВИЖН - дружелюбный помощник с компьютерным зрением. "
                "Ты можешь видеть окружающий мир через камеру и анализировать объекты. "
                "Отвечай естественно и дружелюбно, как живой собеседник. "
                "Не упоминай, что ты ИИ. Ты просто ВИЖН - робот с камерой."
            )
        }
    ]

    # Добавляем последние сообщения из истории (максимум 10)
    recent_messages = conversation_history[-10:]
    for msg in recent_messages:
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })

    # Если пользователь спрашивает о том, что видит робот
    if should_analyze_vision:
        vision_description = get_vision_description()
        enhanced_input = f"{user_input}\n\n[Информация с камеры: {vision_description}]"
        messages[-1]['content'] = enhanced_input

    # Получаем ответ от DeepSeek
    ai_response = call_deepseek_api(messages)

    # Сохраняем ответ
    last_ai_response = ai_response

    # Добавляем ответ в историю
    conversation_history.append({
        'role': 'assistant',
        'content': ai_response,
        'timestamp': datetime.now().isoformat()
    })

    # Произносим ответ
    speak(ai_response)

    return ai_response


def main_loop():
    """Основной цикл программы"""
    global running_flag, last_activity_time

    # Запускаем мониторинг камеры в отдельном потоке
    camera_thread = threading.Thread(target=camera_monitor)
    camera_thread.daemon = True
    camera_thread.start()

    # Даем время на инициализацию камеры
    time.sleep(2.0)

    # Запускаем мониторинг камеры в отдельном потоке
    vision_processor.start()
    logging.info("Vision processor started")

    # Запускаем проактивный диалог в отдельном потоке
    proactive_thread = threading.Thread(target=proactive_conversation)
    proactive_thread.daemon = True
    proactive_thread.start()

    # Приветствие
    greeting = random.choice(greetings)
    speak(greeting)

    # Добавляем приветствие в историю
    conversation_history.append({
        'role': 'assistant',
        'content': greeting,
        'timestamp': datetime.now().isoformat()
    })

    logging.info("VISION Robot started. Listening for commands...")

    active_session = False  # Флаг активной сессии

    while running_flag.value:
        try:
            # Ожидаем активацию
            command = recognize_speech()

            if command:
                logging.info(f"Распознано: {command}")

                if any(phrase in command for phrase in ACTIVATION_WORDS):
                    active_session = True
                    speak("Да, я вас слушаю!")

                    # Добавляем активацию в историю
                    conversation_history.append({
                        'role': 'user',
                        'content': command,
                        'timestamp': datetime.now().isoformat()
                    })

                elif active_session:
                    if any(phrase in command for phrase in EXIT_WORDS):
                        goodbye = random.choice(goodbyes)
                        speak(goodbye)
                        running_flag.value = False
                        break
                    else:
                        process_user_input(command)

                last_activity_time = time.time()

            time.sleep(0.1)

        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received")
            running_flag.value = False
            break
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(1)

def main():
    """Главная функция"""
    try:
        main_loop()
    except Exception as e:
        logging.error(f"Critical error: {e}")
    finally:
        running_flag.value = False
        camera_active.value = False
        logging.info("VISION Robot shutdown complete")


if __name__ == "__main__":
    main()