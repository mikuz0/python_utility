#!/bin/bash

# Скрипт установки FFmpeg и кодеков для Ubuntu 25.10 (Questing)
# С правильными именами пакетов

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

# Установка FFmpeg
print_info "Установка FFmpeg..."
sudo apt install -y ffmpeg libavcodec-extra

# Установка кодеков с правильными именами для 25.10
print_info "Установка кодеков (правильные версии для Ubuntu 25.10)..."

sudo apt install -y \
    libx264-164 \
    libx265-215 \
    libvpx9 \
    libmp3lame0 \
    libopus0 \
    libvorbis0a \
    libfdk-aac2 \
    libdav1d7 \
    libaom3 \
    libxml2-16  # ВАЖНО: не libxml2, а libxml2-16!

# Проверка установки
print_info "Проверка установки..."
if command -v ffmpeg &> /dev/null; then
    FF_VERSION=$(ffmpeg -version | head -n1)
    print_success "FFmpeg установлен: $FF_VERSION"
else
    print_warning "FFmpeg не найден"
fi

print_success "Установка завершена!"
echo
echo "Для проверки кодеков выполните:"
echo "ffmpeg -encoders | grep -E \"libx264|libx265|libmp3lame|libdav1d\""