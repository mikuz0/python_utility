#!/bin/bash

# Скрипт установки Python-зависимостей для Rutube Downloader
# Ubuntu 25.10 (Questing) - правильные имена пакетов

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Проверка sudo
if ! sudo -v; then
    echo "Нужны права sudo"
    exit 1
fi

print_info "Обновление списка пакетов..."
sudo apt update

# Установка Python и базовых зависимостей
print_info "Установка Python и pip (уже есть, проверяем)..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv

# Установка Python-пакетов через apt с правильными именами для 25.10
print_info "Установка Python-пакетов из репозитория..."

# Устанавливаем пакеты по одному с проверкой
install_if_available() {
    if apt-cache show "$1" &>/dev/null; then
        print_info "  Установка $1..."
        sudo apt install -y "$1"
        return 0
    else
        print_warning "  Пакет $1 не найден"
        return 1
    fi
}

# Пробуем разные варианты названий
print_info "Попытка установки python3-requests..."
install_if_available "python3-requests" || \
install_if_available "python3-requests-common" || \
print_warning "requests не найден в apt, будет установлен через pip позже"

print_info "Попытка установки PyQt5..."
install_if_available "python3-pyqt5" || \
install_if_available "pyqt5-dev-tools" || \
install_if_available "python3-pyqt5.qtsvg" || \
print_warning "PyQt5 не найден в apt"

print_info "Попытка установки psutil..."
install_if_available "python3-psutil" || \
print_warning "psutil не найден в apt"

print_info "Попытка установки beautifulsoup4..."
install_if_available "python3-bs4" || \
install_if_available "python3-beautifulsoup4" || \
print_warning "beautifulsoup4 не найден в apt"

print_info "Попытка установки m3u8..."
install_if_available "python3-m3u8" || \
print_warning "m3u8 не найден в apt"

# Установка оставшихся пакетов через pip
print_info "Установка недостающих пакетов через pip..."
MISSING_PKGS=""

if ! python3 -c "import requests" 2>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS requests"
fi

if ! python3 -c "import PyQt5" 2>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS PyQt5"
fi

if ! python3 -c "import psutil" 2>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS psutil"
fi

if ! python3 -c "import bs4" 2>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS beautifulsoup4"
fi

if ! python3 -c "import m3u8" 2>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS m3u8"
fi

if [ -n "$MISSING_PKGS" ]; then
    print_info "Установка через pip:$MISSING_PKGS"
    pip3 install --user $MISSING_PKGS
fi

# Финальная проверка
print_info "Проверка установленных пакетов..."

check_package() {
    if python3 -c "import $1" 2>/dev/null; then
        print_success "  ✓ $1"
        return 0
    else
        print_warning "  ✗ $1"
        return 1
    fi
}

check_package "requests"
check_package "PyQt5"
check_package "psutil"
check_package "bs4"
check_package "m3u8"

print_success "Установка Python-зависимостей завершена!"
echo
echo "Для запуска программы используйте:"
echo "python3 main.py"