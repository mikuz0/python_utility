#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DPCreator Analyzer")
    app.setOrganizationName("DPCreator")
    
    # Загрузка стилей
    style_file = os.path.join(os.path.dirname(__file__), "resources", "styles.qss")
    if os.path.exists(style_file):
        with open(style_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()