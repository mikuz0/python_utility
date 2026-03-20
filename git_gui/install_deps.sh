#!/bin/bash
# install_deps.sh

echo "Установка зависимостей для Git GUI..."

# Обновление списка пакетов
sudo apt update

# Установка необходимых пакетов
sudo apt install -y \
    python3 \
    python3-tk \
    python3-git \
    python3-pil \
    python3-pil.imagetk \
    python3-gi \
    python3-gi-cairo \
    git

echo "Зависимости установлены!"

# Проверка установки
echo ""
echo "Проверка установленных модулей:"

python3 -c "import git; print('✅ GitPython')" 2>/dev/null || echo "❌ GitPython"
python3 -c "from PIL import Image; print('✅ PIL')" 2>/dev/null || echo "❌ PIL"
python3 -c "from PIL import ImageTk; print('✅ ImageTk')" 2>/dev/null || echo "❌ ImageTk"
python3 -c "import tkinter; print('✅ Tkinter')" 2>/dev/null || echo "❌ Tkinter"

echo ""
echo "Готово! Запустите программу: python3 main.py"