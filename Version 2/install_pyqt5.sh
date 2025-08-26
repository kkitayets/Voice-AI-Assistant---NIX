#!/bin/bash

# Установка зависимостей Homebrew
brew install pkg-config qt@5

# Установка Python зависимостей
pip install --upgrade pip
pip install PyQt5-sip
pip install PyQt5

# Проверка установки
python -c "from PyQt5 import QtWidgets; print('PyQt5 успешно установлен!')"