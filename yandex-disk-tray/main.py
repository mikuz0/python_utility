#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
from PyQt6.QtWidgets import QApplication, QMessageBox
from tray_icon import YandexDiskTray

def main():
    # Проверяем наличие yandex-disk
    try:
        result = subprocess.run("which yandex-disk", shell=True, capture_output=True, text=True)
        if not result.stdout:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("yandex-disk не установлен!")
            msg_box.setInformativeText(
                "Установите его:\n"
                "sudo apt install yandex-disk  # для Ubuntu/Debian\n"
                "или скачайте с https://disk.yandex.ru/download"
            )
            msg_box.exec()
            sys.exit(1)
    except:
        pass
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    tray = YandexDiskTray(app)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()