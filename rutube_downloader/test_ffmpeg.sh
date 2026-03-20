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
