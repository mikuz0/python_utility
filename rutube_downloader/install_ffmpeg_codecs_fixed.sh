#!/bin/bash

# Скрипт установки FFmpeg и кодеков из apt
# Исправленная версия для Ubuntu 24.04

set -e  # Прерывать при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав sudo
check_sudo() {
    print_info "Проверка прав sudo..."
    if ! sudo -v; then
        print_error "Не удалось получить права sudo. Скрипт требует sudo для установки пакетов."
        exit 1
    fi
    print_success "Права sudo получены"
}

# Проверка версии Ubuntu
get_ubuntu_version() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        UBUNTU_VERSION=$VERSION_ID
        print_info "Обнаружена Ubuntu $UBUNTU_VERSION"
    else
        UBUNTU_VERSION="22.04"
        print_warning "Не удалось определить версию, предполагаем Ubuntu 22.04"
    fi
}

# Обновление списка пакетов
update_package_list() {
    print_info "Обновление списка пакетов..."
    sudo apt update
    print_success "Список пакетов обновлен"
}

# Установка FFmpeg и основных кодеков
install_ffmpeg() {
    print_info "Установка FFmpeg и базовых кодеков..."
    
    # Удаляем старый libavcodec61 если он мешает
    if dpkg -l | grep -q libavcodec61; then
        print_info "Удаление libavcodec61..."
        sudo apt remove -y libavcodec61
    fi
    
    # Устанавливаем FFmpeg с extra-кодеками
    sudo apt install -y ffmpeg libavcodec-extra
    
    print_success "FFmpeg установлен"
}

# Установка видео кодеков (адаптировано для Ubuntu 24.04)
install_video_codecs() {
    print_info "Установка видео кодеков..."
    
    # Базовые видео кодеки
    sudo apt install -y \
        libx264-dev \
        libx265-dev \
        libvpx-dev \
        libtheora-dev \
        libxvidcore-dev
    
    # AV1 кодеки (с проверкой доступности)
    if apt-cache show libaom-dev &>/dev/null; then
        sudo apt install -y libaom-dev
    else
        print_warning "libaom-dev не найден, пропускаем"
    fi
    
    if apt-cache show libdav1d-dev &>/dev/null; then
        sudo apt install -y libdav1d-dev
    else
        print_warning "libdav1d-dev не найден, пропускаем"
    fi
    
    # Для Ubuntu 24.04 libsvtav1-dev может называться по-другому
    if apt-cache show libsvtav1enc-dev &>/dev/null; then
        sudo apt install -y libsvtav1enc-dev
        print_success "Установлен libsvtav1enc-dev"
    elif apt-cache show libsvtav1-dev &>/dev/null; then
        sudo apt install -y libsvtav1-dev
        print_success "Установлен libsvtav1-dev"
    else
        print_warning "Пакет SVT-AV1 не найден, пропускаем"
    fi
    
    print_success "Видео кодеки установлены"
}

# Установка аудио кодеков
install_audio_codecs() {
    print_info "Установка аудио кодеков..."
    
    sudo apt install -y \
        libmp3lame-dev \
        libopus-dev \
        libvorbis-dev \
        libspeex-dev \
        libtwolame-dev \
        libwavpack-dev \
        libgsm1-dev \
        libopencore-amrnb-dev \
        libopencore-amrwb-dev
    
    # FDK-AAC (может быть в разных репозиториях)
    if apt-cache show libfdk-aac-dev &>/dev/null; then
        sudo apt install -y libfdk-aac-dev
    else
        print_warning "libfdk-aac-dev не найден, пропускаем"
    fi
    
    print_success "Аудио кодеки установлены"
}

# Установка дополнительных библиотек
install_extra_libs() {
    print_info "Установка дополнительных библиотек..."
    
    sudo apt install -y \
        libass-dev \
        libfreetype6-dev \
        libfontconfig1-dev \
        libsdl2-dev \
        libva-dev \
        libvdpau-dev \
        libdrm-dev \
        libnuma-dev \
        libssl-dev \
        libbluray-dev \
        libzmq3-dev \
        libopenjp2-7-dev \
        libwebp-dev \
        librtmp-dev \
        libssh-dev \
        libxml2-dev \
        libsoxr-dev
    
    print_success "Дополнительные библиотеки установлены"
}

# Установка аппаратного ускорения для AMD
install_amd_support() {
    print_info "Установка поддержки аппаратного ускорения для AMD..."
    
    sudo apt install -y \
        mesa-va-drivers \
        mesa-vdpau-drivers \
        va-driver-all \
        vdpau-driver-all \
        libva2 \
        libvdpau1 \
        vainfo \
        vdpauinfo || {
        print_warning "Некоторые пакеты AMD не удалось установить"
        # Пробуем установить по частям
        sudo apt install -y mesa-va-drivers vainfo || true
        sudo apt install -y mesa-vdpau-drivers vdpauinfo || true
    }
    
    print_success "Поддержка AMD установлена (где возможно)"
}

# Проверка установки
verify_installation() {
    print_info "Проверка установки..."
    
    # Проверка FFmpeg
    if command -v ffmpeg &> /dev/null; then
        FF_VERSION=$(ffmpeg -version | head -n1)
        print_success "✓ FFmpeg: $FF_VERSION"
    else
        print_error "✗ FFmpeg не установлен"
        return 1
    fi
    
    # Проверка основных кодеков
    print_info "Проверка кодеков в FFmpeg:"
    
    # Основные кодеки которые должны быть
    CODECS=("libx264" "libx265" "libvpx" "libmp3lame" "libopus" "aac")
    
    for codec in "${CODECS[@]}"; do
        if ffmpeg -encoders 2>/dev/null | grep -q "$codec"; then
            print_success "  ✓ $codec"
        else
            print_warning "  ✗ $codec"
        fi
    done
}

# Создание тестового скрипта
create_test_script() {
    cat > test_ffmpeg.sh << 'EOF'
#!/bin/bash

echo "==================================="
echo "    Проверка FFmpeg и кодеков"
echo "==================================="
echo

# Версия
echo "📦 Версия FFmpeg: $(ffmpeg -version | head -n1)"
echo

# Основные кодеки
echo "🎬 Доступные кодеки:"
echo "-------------------"

# H.264
if ffmpeg -encoders 2>/dev/null | grep -q libx264; then
    echo "  ✅ H.264 (libx264)"
else
    echo "  ❌ H.264"
fi

# H.265
if ffmpeg -encoders 2>/dev/null | grep -q libx265; then
    echo "  ✅ H.265 (libx265)"
else
    echo "  ❌ H.265"
fi

# VP9
if ffmpeg -encoders 2>/dev/null | grep -q libvpx; then
    echo "  ✅ VP9 (libvpx)"
else
    echo "  ❌ VP9"
fi

# MP3
if ffmpeg -encoders 2>/dev/null | grep -q libmp3lame; then
    echo "  ✅ MP3 (libmp3lame)"
else
    echo "  ❌ MP3"
fi

# AAC
if ffmpeg -encoders 2>/dev/null | grep -q aac; then
    echo "  ✅ AAC"
else
    echo "  ❌ AAC"
fi

# Opus
if ffmpeg -encoders 2>/dev/null | grep -q libopus; then
    echo "  ✅ Opus"
else
    echo "  ❌ Opus"
fi

echo
echo "✅ Проверка завершена"
EOF

    chmod +x test_ffmpeg.sh
    print_success "Создан тестовый скрипт test_ffmpeg.sh"
}

# Главная функция
main() {
    echo "========================================="
    echo "  Установка FFmpeg и кодеков"
    echo "  (адаптировано для Ubuntu 24.04)"
    echo "========================================="
    echo
    
    check_sudo
    get_ubuntu_version
    update_package_list
    
    # Основная установка
    install_ffmpeg
    install_video_codecs
    install_audio_codecs
    install_extra_libs
    
    # Опционально: аппаратное ускорение
    echo
    read -p "Установить поддержку аппаратного ускорения для AMD? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_amd_support
    fi
    
    # Создание тестового скрипта
    create_test_script
    
    # Проверка
    echo
    verify_installation
    
    echo
    echo "========================================="
    print_success "Установка завершена!"
    echo "========================================="
    echo
    echo "Для проверки выполните:"
    echo "  ./test_ffmpeg.sh"
    echo
}

# Запуск
main "$@"