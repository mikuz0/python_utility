#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="yandex-disk-tray",
    version="1.0.0",
    description="GUI для Яндекс.Диска в системном трее",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
    ],
    entry_points={
        "console_scripts": [
            "yandex-disk-tray=main:main",
        ],
    },
    python_requires=">=3.6",
)