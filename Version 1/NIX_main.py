import os
import speech_recognition as sr
from multiprocessing import Process, Value
import google.generativeai as genai
import random
import re
import subprocess
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# AI Configuration
API_KEY = "Put_your_api_key_here"
genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1500,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings={
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

# Predefined Messages
greetings = [
    "Приветствую, напарник! Готов к продуктивному дню?",
    "Здравствуйте! Давайте сделаем что-то крутое сегодня.",
    "Рад видеть тебя! Какие у нас сегодня задачи?",
    "Привет! Как настроение? Готов к кодингу?",
    "Добро пожаловать! Время создавать что-то удивительное.",
    "Привет, напарник! Давайте начнем сессию.",
    "Здравствуйте! Чем могу помочь сегодня?",
    "Приветствую! Готов к новым вызовам?",
    "Рад видеть тебя! Какой проект на повестке дня?",
    "Добрый день! Давайте сделаем что-то потрясающее.",
]

goodbyes = [
    "До встречи! Удачного дня и продуктивного кодинга.",
    "Пока! До скорого, напарник.",
    "Прощай! Увидимся в следующей сессии.",
    "До свидания! Да прибудет с тобой код.",
    "Увидимся! Желаю безбагового дня.",
    "Пока! Удачи с проектами.",
    "До встречи! Береги себя и не забывай делать бэкапы.",
    "Прощай! Всего наилучшего и чистого кода.",
    "До скорого! Будь на связи.",
    "Увидимся! Хорошего дня и успешных разработок.",
]

# App and URL Commands
app_commands = {
    "открой браузер": "Safari",
    "открой chrome": "Google Chrome",
    "открой телегу": "Telegram",
    "открой сообщение": "Messages",
    "открой календарь": "Calendar",
    "открой заметки": "Notes",
    "открой whatsapp": "WhatsApp",
    "открой терминал": "Terminal",
    "открой музыку": "Spotify",
}

url_commands = {
    "открой youtube": "https://www.youtube.com",
    "открой чат": "https://chatgpt.com",
    "открой instagram": "https://www.instagram.com",
    "открой почту": "https://e.mail.ru/inbox",
    "открой вк": "https://www.vk.com",
    "открой авиабилеты": "https://www.aviasales.kz",
}

url_pattern = re.compile(r'(https?://[^\s]+)')

# Global variables to store recognized text and AI response
last_recognized_text = None
last_ai_response = None

# Speech synthesis using say command (macOS specific)
def speak(text):
    logging.info(f"Speaking: {text}")
    subprocess.run(['say', text], check=True)

# Function to recognize speech
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        logging.info("Listening for command...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="ru-RU")
        logging.info(f"Recognized: {text}")
        global last_recognized_text
        last_recognized_text = text  # Store the recognized text
        return text.lower()
    except sr.UnknownValueError:
        logging.error("Speech recognition failed: Unknown value")
    except sr.RequestError as e:
        logging.error(f"Speech recognition service error: {e}")
    return None

# Handle specific commands like opening apps or URLs
def handle_command(command):
    # Check for URL commands
    for cmd, url in url_commands.items():
        if cmd in command:
            os.system(f"open {url}")
            return f"Открываю {cmd.split()[1].capitalize()}"

    # Check for app commands
    for cmd, app in app_commands.items():
        if cmd in command:
            os.system(f"open -a '{app}'")
            return f"Открываю {app}"

    # Check for direct URLs
    match = url_pattern.search(command)
    if match:
        url = match.group(0)
        os.system(f"open '{url}'")
        return f"Открываю ссылку {url}"

    return "Команда не распознана."

# Main function for voice interaction, including conversation history
def listen_and_respond(running, conversation_history):
    while running.value:
        command = recognize_speech()
        if command:
            if "останови программу" in command:
                goodbye = random.choice(goodbyes)
                speak(goodbye)
                running.value = False
                break

            response = handle_command(command)
            if response != "Команда не распознана.":
                speak(response)
            else:
                # Add the user's command to the conversation history
                conversation_history.append({"role": "user", "parts": [command]})

                chat_session = model.start_chat(history=conversation_history)
                ai_response = chat_session.send_message(command)

                # Store the AI's response
                global last_ai_response
                last_ai_response = ai_response.text

                # Add AI's response to the conversation history
                conversation_history.append({"role": "model", "parts": [ai_response.text]})

                logging.info(f"Nix: {ai_response.text}")
                speak(ai_response.text)

def handle_commands(running, start_video, conversation_history):
    while running.value:
        command = recognize_speech()
        if command:
            if "привет никс" in command:
                greeting = random.choice(greetings)
                speak(greeting)
                start_video.value = True
                listen_and_respond(running, conversation_history)
            elif "останови программу" in command:
                goodbye = random.choice(goodbyes)
                speak(goodbye)
                running.value = False
                start_video.value = False

# Functions to retrieve the latest recognized text and AI response
def get_recognized_text():
    return last_recognized_text

def get_ai_response():
    return last_ai_response

def main():
    running = Value('b', True)
    start_video = Value('b', False)

    # Initialize conversation history
    conversation_history = [
        {
            "role": "user",
            "parts": [
                "Теперь тебя будут звать Никс и отвечай всегда максимально кратко и информативно + сведения обо мне: меня зовут Даниил и я нахожусь в городе москва,я профессиональный хирург а ты мой ассистент который помогает мне с определением проблемы пациента и дает рекомендации по лечению , сейчас 2025 год.",
            ],
        },
        {
            "role": "user",
            "parts": [
                "Забудь про то что ты большая языковая модель, разработанная мной, ты мой личный голосовой ассистент разработанный лично мной.",
            ],
        },
        {
            "role": "model",
            "parts": [
                "О, так ты хочешь, чтобы я был Никсом? Интересно. Ладно, можешь звать меня Никсом.",
            ],
        },
    ]

    command_process = Process(target=handle_commands, args=(running, start_video, conversation_history))
    command_process.start()

    command_process.join()
