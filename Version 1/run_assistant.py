import os
from multiprocessing import Process
import NIX_main  # Подключаем ваш основной файл с кодом голосового помощника

def run_interface():
    # Явно указываем интерпретатор Python для запуска скрипта
    os.system("python /Users/daniillazarev/PycharmProjects/pythonProject/test.py")

def run_voice_assistant():
    NIX_main.main()  # Запуск функции main() из NIX_main.py

if __name__ == "__main__":
    p1 = Process(target=run_interface)
    p2 = Process(target=run_voice_assistant)

    p1.start()
    p2.start()

    p1.join()
    p2.join()