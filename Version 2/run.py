import os
import sys
import time
import logging
import threading
import subprocess
from multiprocessing import Process
import signal
import platform
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vision_robot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
def check_dependencies():
    required_packages = [
        'cv2', 'numpy', 'speech_recognition', 'requests',
        'ultralytics', 'PyQt5'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PyQt5':
                import PyQt5
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        logger.error(f"Отсутствуют зависимости: {', '.join(missing_packages)}")
        logger.info("Установите зависимости командой:")
        logger.info("pip install opencv-python numpy SpeechRecognition requests ultralytics PyQt5")
        return False

    return True


def check_system_requirements():
    logger.info("Проверка системных требований...")

    # Проверка камеры
    import cv2
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.warning("Камера не найдена или недоступна")
        return False
    cap.release()

    # Проверка микрофона (базовая проверка)
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            pass
        logger.info("Микрофон доступен")
    except Exception as e:
        logger.warning(f"Проблема с микрофоном: {e}")

    # Проверка системы синтеза речи
    if sys.platform == "darwin":  # macOS
        result = subprocess.run(['which', 'say'], capture_output=True)
        if result.returncode != 0:
            logger.warning("Команда 'say' не найдена. Синтез речи может не работать.")
    elif sys.platform == "win32":  # Windows
        logger.info("На Windows используется встроенный синтез речи")
    else:  # Linux
        result = subprocess.run(['which', 'espeak'], capture_output=True)
        if result.returncode != 0:
            logger.warning("Команда 'espeak' не найдена. Установите espeak для синтеза речи.")

    return True


def check_config():
    logger.info("Проверка конфигурации...")

    try:
        from config import OPENROUTER_API_KEY
        if OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY_HERE":
            logger.error("Не установлен API ключ OpenRouter!")
            logger.info("Отредактируйте файл config.py и установите ваш API ключ")
            return False
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки конфигурации: {e}")
        return False


def install_requirements():
    logger.info("Установка зависимостей...")

    packages = [
        'opencv-python',
        'numpy',
        'SpeechRecognition',
        'requests',
        'ultralytics',
        'PyQt5'
    ]

    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            logger.info(f"Установлен пакет: {package}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка установки пакета {package}: {e}")
            return False

    return True


def download_yolo_model():
    """Загрузка модели YOLO"""
    logger.info("Проверка модели YOLO...")

    try:
        from ultralytics import YOLO
        # Это автоматически загрузит модель, если она не существует
        model = YOLO('yolov8n.pt')
        logger.info("Модель YOLO готова к использованию")
        return True
    except Exception as e:
        logger.error(f"Ошибка загрузки модели YOLO: {e}")
        return False


def setup_speech_recognition():
    """Настройка распознавания речи"""
    logger.info("Настройка распознавания речи...")

    system = platform.system()

    if system == "Darwin":  # macOS
        logger.info("Используется встроенная система распознавания речи macOS")
        return True
    elif system == "Windows":
        logger.info("Используется встроенная система распознавания речи Windows")
        return True
    elif system == "Linux":
        # Проверяем наличие необходимых пакетов для Linux
        try:
            subprocess.check_call(['which', 'espeak'], stdout=subprocess.DEVNULL)
            logger.info("Система синтеза речи espeak найдена")
        except subprocess.CalledProcessError:
            logger.warning("espeak не найден. Установите: sudo apt install espeak")

    return True


def run_main_process():
    """Запуск основного процесса робота"""
    logger.info("Запуск основного процесса VISION Robot...")
    try:
        import main
        main.main()
    except Exception as e:
        logger.error(f"Ошибка в основном процессе: {e}")


def run_interface():
    """Запуск интерфейса"""
    logger.info("Запуск интерфейса...")
    try:
        import interface
        interface.main()
    except Exception as e:
        logger.error(f"Ошибка в интерфейсе: {e}")


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info("Получен сигнал завершения. Останавливаем систему...")
    sys.exit(0)


def show_menu():
    """Показать меню выбора"""
    print("\n" + "=" * 60)
    print("🤖 VISION Robot - Система запуска")
    print("=" * 60)
    print("Выберите режим запуска:")
    print("1. 🎤 Только основной процесс (голосовое управление)")
    print("2. 🖥️  Только интерфейс (GUI)")
    print("3. 🚀 Полная система (основной процесс + интерфейс)")
    print("4. 🛠️  Установить зависимости")
    print("5. 🔧 Настроить систему")
    print("6. ❌ Выход")
    print("=" * 60)


def setup_system():
    """Настройка системы"""
    logger.info("Настройка системы VISION Robot...")

    print("\n🔧 Настройка системы...")

    # Установка зависимостей
    if not install_requirements():
        logger.error("Ошибка установки зависимостей")
        return False

    # Загрузка модели YOLO
    if not download_yolo_model():
        logger.error("Ошибка загрузки модели YOLO")
        return False

    # Настройка распознавания речи
    if not setup_speech_recognition():
        logger.error("Ошибка настройки распознавания речи")
        return False

    logger.info("Система успешно настроена!")
    return True


def main():
    """Главная функция запуска"""
    logger.info("=" * 60)
    logger.info("VISION Robot - Запуск системы")
    logger.info("=" * 60)

    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        show_menu()
        choice = input("\nВведите номер (1-6): ").strip()

        if choice == "1":
            logger.info("Режим: Только основной процесс")

            # Проверяем зависимости
            if not check_dependencies():
                logger.error("Проверка зависимостей не пройдена!")
                continue

            # Проверяем системные требования
            if not check_system_requirements():
                logger.error("Проверка системных требований не пройдена!")
                continue

            # Проверяем конфигурацию
            if not check_config():
                logger.error("Проверка конфигурации не пройдена!")
                continue

            logger.info("Все проверки пройдены. Запуск основного процесса...")
            run_main_process()
            break

        elif choice == "2":
            logger.info("Режим: Только интерфейс")

            # Проверяем зависимости
            if not check_dependencies():
                logger.error("Проверка зависимостей не пройдена!")
                continue

            logger.info("Запуск интерфейса...")
            run_interface()
            break

        elif choice == "3":
            logger.info("Режим: Полная система")

            # Проверяем зависимости
            if not check_dependencies():
                logger.error("Проверка зависимостей не пройдена!")
                continue

            # Проверяем системные требования
            if not check_system_requirements():
                logger.error("Проверка системных требований не пройдена!")
                continue

            # Проверяем конфигурацию
            if not check_config():
                logger.error("Проверка конфигурации не пройдена!")
                continue

            logger.info("Все проверки пройдены. Запуск полной системы...")

            # Запускаем основной процесс в отдельном потоке
            main_thread = threading.Thread(target=run_main_process, daemon=True)
            main_thread.start()

            # Даем время на инициализацию
            time.sleep(2)

            # Запускаем интерфейс в основном потоке
            run_interface()
            break

        elif choice == "4":
            logger.info("Режим: Установка зависимостей")
            if install_requirements():
                logger.info("Зависимости успешно установлены!")
            else:
                logger.error("Ошибка установки зависимостей")

        elif choice == "5":
            logger.info("Режим: Настройка системы")
            if setup_system():
                logger.info("Система успешно настроена!")
            else:
                logger.error("Ошибка настройки системы")

        elif choice == "6":
            logger.info("Выход из программы")
            break

        else:
            print("❌ Неверный выбор. Попробуйте снова.")

    logger.info("VISION Robot - Завершение работы")
    return 0


if __name__ == "__main__":
    sys.exit(main())