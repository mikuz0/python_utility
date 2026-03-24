#!/bin/bash

# Скрипт для анализа зависимостей бинарного файла и определения deb-пакетов
# Использование: sudo ./analyze_libs.sh <путь_к_бинарному_файлу> [выходной_файл]

# Функция для вывода справки
show_help() {
    cat << EOF
Использование: sudo $0 <путь_к_бинарному_файлу> [выходной_файл]

Анализирует зависимости бинарного файла и определяет deb-пакеты.
Для корректной работы рекомендуется запуск с sudo.

Аргументы:
    <путь_к_бинарному_файлу>    - путь к анализируемому бинарному файлу
    [выходной_файл]             - опциональный путь к выходному файлу

Пример:
    sudo $0 /usr/bin/python3
    sudo $0 /bin/ls ./my_analysis.txt
EOF
    exit 0
}

# Проверка аргументов
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
fi

if [ $# -lt 1 ]; then
    echo "Ошибка: Не указан путь к бинарному файлу"
    show_help
fi

BINARY_FILE="$1"

# Проверка существования бинарного файла
if [ ! -f "$BINARY_FILE" ]; then
    echo "Ошибка: Файл '$BINARY_FILE' не существует"
    exit 1
fi

# Формируем имя выходного файла
if [ -n "$2" ]; then
    OUTPUT_FILE="$2"
else
    BASE_NAME=$(basename "$BINARY_FILE")
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    OUTPUT_FILE="analysis_${BASE_NAME}_${TIMESTAMP}.txt"
fi

# Создаем временные файлы
TEMP_DIR=$(mktemp -d)
LDD_OUTPUT="$TEMP_DIR/ldd_output.txt"
LIBS_LIST="$TEMP_DIR/libs_list.txt"
DEB_PACKAGES_RAW="$TEMP_DIR/deb_packages_raw.txt"
FINAL_PACKAGES="$TEMP_DIR/final_packages.txt"
LIB_TO_PACKAGE="$TEMP_DIR/lib_to_package.txt"

# Функция очистки временных файлов
cleanup() {
    rm -rf "$TEMP_DIR"
}

trap cleanup EXIT

# Улучшенная функция для получения пакета с обработкой символических ссылок
get_package() {
    local file="$1"
    local pkg=""
    local resolved_file=""
    local lib_name=""
    
    # Получаем реальный путь (разрешаем все символические ссылки)
    if [ -L "$file" ]; then
        resolved_file=$(readlink -f "$file" 2>/dev/null)
    else
        resolved_file="$file"
    fi
    
    # Если файл существует
    if [ -n "$resolved_file" ] && [ -e "$resolved_file" ]; then
        # Способ 1: dpkg -S с реальным путем
        pkg=$(sudo dpkg -S "$resolved_file" 2>/dev/null | head -n 1 | cut -d: -f1)
        [ -n "$pkg" ] && { echo "$pkg"; return 0; }
        
        # Способ 2: dpkg -S с оригинальным путем
        pkg=$(sudo dpkg -S "$file" 2>/dev/null | head -n 1 | cut -d: -f1)
        [ -n "$pkg" ] && { echo "$pkg"; return 0; }
        
        # Способ 3: Поиск по имени файла (для библиотек из libc6)
        lib_name=$(basename "$resolved_file")
        # Убираем суффикс версии для поиска (libc.so.6 -> libc.so)
        lib_base="${lib_name%%.so*}.so"
        
        # Ищем пакет, содержащий файл с таким именем
        pkg=$(sudo dpkg -S "*$lib_base*" 2>/dev/null | grep -E ".*$lib_name" | head -n 1 | cut -d: -f1)
        [ -n "$pkg" ] && { echo "$pkg"; return 0; }
        
        # Способ 4: Используем apt-file если доступен
        if command -v apt-file &> /dev/null; then
            pkg=$(apt-file search "$lib_name" 2>/dev/null | head -n 1 | cut -d: -f1)
            [ -n "$pkg" ] && { echo "$pkg"; return 0; }
        fi
        
        # Способ 5: Специальные случаи для часто встречающихся библиотек
        case "$lib_name" in
            libc.so.*|libm.so.*|libresolv.so.*|libnss_*.so*)
                echo "libc6"
                return 0
                ;;
            libgcc_s.so.*)
                echo "libgcc-s1"
                return 0
                ;;
            libcrypto.so.*)
                echo "libssl3"
                return 0
                ;;
            libstdc++.so.*)
                echo "libstdc++6"
                return 0
                ;;
            libz.so.*)
                echo "zlib1g"
                return 0
                ;;
        esac
    fi
    
    echo "unknown"
    return 1
}

# Начинаем запись в выходной файл
exec > >(tee "$OUTPUT_FILE") 2>&1

echo "=========================================="
echo "Анализ зависимостей бинарного файла"
echo "=========================================="
echo "Дата и время: $(date)"
echo "Бинарный файл: $BINARY_FILE"
echo "Выходной файл: $OUTPUT_FILE"
echo "=========================================="
echo ""

# Шаг 1: Анализ библиотек с помощью ldd
echo "Шаг 1: Анализ библиотек с помощью ldd"
echo "----------------------------------------"
echo "Выполняется команда: ldd \"$BINARY_FILE\""
echo ""

if ldd "$BINARY_FILE" > "$LDD_OUTPUT" 2>&1; then
    echo "✓ Утилита ldd успешно выполнилась"
else
    echo "✗ Ошибка при выполнении ldd"
    cat "$LDD_OUTPUT"
    exit 1
fi

echo ""
echo "Содержимое ldd (первые 20 строк):"
echo "---"
head -n 20 "$LDD_OUTPUT"
echo "---"
echo ""

# Шаг 2: Извлечение путей к библиотекам
echo "Шаг 2: Извлечение путей к библиотекам"
echo "----------------------------------------"

# Извлекаем все пути библиотек из ldd
grep -E "(=>|^[[:space:]]*/)" "$LDD_OUTPUT" | grep -v "linux-vdso" | while read line; do
    if echo "$line" | grep -q "=>"; then
        echo "$line" | awk -F'=>' '{print $2}' | awk '{print $1}'
    else
        echo "$line" | awk '{print $1}'
    fi
done | grep -v "^[[:space:]]*$" | sort -u > "$LIBS_LIST"

if [ ! -s "$LIBS_LIST" ]; then
    echo "✗ Не найдено ни одной библиотеки для анализа"
    exit 1
fi

LIB_COUNT=$(wc -l < "$LIBS_LIST")
echo "✓ Найдено уникальных библиотек: $LIB_COUNT"
echo ""

# Шаг 3: Проверка существования и определение пакетов
echo "Шаг 3: Проверка существования файлов библиотек и определение deb-пакетов"
echo "------------------------------------------------------------------------"
echo "Примечание: Для каждой библиотеки показывается:"
echo "  - статус файла и его реальный путь"
echo "  - найденный пакет"
echo "---"

# Инициализируем файлы
> "$DEB_PACKAGES_RAW"
> "$LIB_TO_PACKAGE"
> "$FINAL_PACKAGES"

EXISTING_COUNT=0
MISSING_COUNT=0
UNKNOWN_COUNT=0
CURRENT=0

echo ""
echo "Анализ каждой библиотеки:"
echo "---"

while IFS= read -r lib; do
    CURRENT=$((CURRENT + 1))
    
    lib=$(echo "$lib" | xargs)
    [ -z "$lib" ] && continue
    
    lib_name=$(basename "$lib")
    echo -n "[$CURRENT/$LIB_COUNT] $lib_name"
    
    # Получаем реальный путь
    real_lib=$(readlink -f "$lib" 2>/dev/null)
    [ -z "$real_lib" ] && real_lib="$lib"
    
    # Проверяем существование
    if [ -e "$real_lib" ]; then
        if [ "$real_lib" != "$lib" ]; then
            echo -n " -> ссылка -> $(basename "$real_lib")"
        else
            echo -n " -> файл"
        fi
        
        # Определяем пакет
        pkg=$(get_package "$lib")
        
        if [ "$pkg" != "unknown" ]; then
            echo " -> ✓ ПАКЕТ: $pkg"
            echo "$lib|$pkg" >> "$LIB_TO_PACKAGE"
            echo "$pkg" >> "$DEB_PACKAGES_RAW"
            ((EXISTING_COUNT++))
        else
            echo " -> ❌ ПАКЕТ НЕ НАЙДЕН"
            echo "$lib|unknown" >> "$LIB_TO_PACKAGE"
            ((UNKNOWN_COUNT++))
        fi
    else
        echo " -> ❌ ФАЙЛ НЕ НАЙДЕН"
        ((MISSING_COUNT++))
        echo "$lib|not_found" >> "$LIB_TO_PACKAGE"
    fi
done < "$LIBS_LIST"

echo ""
echo "Статистика:"
echo "  ✓ Найдено пакетов: $EXISTING_COUNT"
echo "  ✗ Отсутствующих файлов: $MISSING_COUNT"
echo "  ? Пакетов не найдено: $UNKNOWN_COUNT"
echo ""

# Шаг 4: Формирование уникального списка пакетов
echo "Шаг 4: Формирование уникального списка deb-пакетов"
echo "------------------------------------------------"

if [ -s "$DEB_PACKAGES_RAW" ]; then
    sort -u "$DEB_PACKAGES_RAW" > "$FINAL_PACKAGES"
    PACKAGE_COUNT=$(wc -l < "$FINAL_PACKAGES")
    echo "✓ Сформирован список уникальных пакетов"
    echo "  Всего уникальных пакетов: $PACKAGE_COUNT"
else
    PACKAGE_COUNT=0
    echo "⚠ Не найдено ни одного пакета"
fi
echo ""

# Шаг 5: Вывод итогового списка
echo "=========================================="
echo "ИТОГОВЫЙ СПИСОК DEB-ПАКЕТОВ (УНИКАЛЬНЫЕ)"
echo "=========================================="
echo ""

if [ $PACKAGE_COUNT -gt 0 ]; then
    echo "Список пакетов (каждый пакет указан один раз):"
    echo "---"
    cat "$FINAL_PACKAGES"
    echo "---"
    echo ""
    echo "Всего: $PACKAGE_COUNT пакетов"
fi
echo ""

# Сохраняем список пакетов
PACKAGES_ONLY="${OUTPUT_FILE%.txt}_packages.txt"
cp "$FINAL_PACKAGES" "$PACKAGES_ONLY" 2>/dev/null || touch "$PACKAGES_ONLY"

# Детальная информация
if [ $EXISTING_COUNT -gt 0 ]; then
    echo ""
    echo "=========================================="
    echo "ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ЗАВИСИМОСТЯХ"
    echo "=========================================="
    echo ""
    echo "Формат: Библиотека -> Пакет"
    echo "---"
    while IFS='|' read -r lib pkg; do
        if [ "$pkg" != "unknown" ] && [ "$pkg" != "not_found" ]; then
            printf "  %-50s -> %s\n" "$(basename "$lib")" "$pkg"
        fi
    done < "$LIB_TO_PACKAGE"
fi

echo ""
echo "=========================================="
echo "СТАТИСТИКА АНАЛИЗА"
echo "=========================================="
echo "Всего найдено библиотек: $LIB_COUNT"
echo "  - С найденными пакетами: $EXISTING_COUNT"
echo "  - Отсутствующих файлов: $MISSING_COUNT"
echo "  - Без найденного пакета: $UNKNOWN_COUNT"
echo "Уникальных пакетов: $PACKAGE_COUNT"
echo ""

# Вывод Qt пакетов
if [ $PACKAGE_COUNT -gt 0 ]; then
    echo "=========================================="
    echo "QT ПАКЕТЫ"
    echo "=========================================="
    grep -i "qt" "$FINAL_PACKAGES" 2>/dev/null || echo "Qt пакеты не найдены"
    echo ""
fi

echo "=========================================="
echo "Анализ завершен. Результаты сохранены в:"
echo "  - Полный отчет: $OUTPUT_FILE"
echo "  - Список уникальных пакетов: $PACKAGES_ONLY"
echo "=========================================="