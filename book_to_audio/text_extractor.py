import os
from pathlib import Path
import PyPDF2
from ebooklib import epub
from bs4 import BeautifulSoup
import re

class TextExtractor:
    """Извлечение текста из различных форматов"""
    
    SUPPORTED_FORMATS = {
        '.txt': 'text/plain',
        '.pdf': 'application/pdf',
        '.epub': 'application/epub+zip',
        '.fb2': 'application/fb2'
    }
    
    def __init__(self, work_dir):
        self.work_dir = Path(work_dir)
        self.extracted_dir = self.work_dir / "01_extracted_text"
        self.extracted_dir.mkdir(exist_ok=True)
    
    def extract_from_txt(self, file_path):
        """Извлечение из текстового файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_from_pdf(self, file_path):
        """Извлечение из PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Страница {page_num + 1} ---\n{page_text}"
        except Exception as e:
            print(f"Ошибка чтения PDF {file_path}: {e}")
            return ""
        return text
    
    def extract_from_epub(self, file_path):
        """Извлечение из EPUB"""
        text = ""
        try:
            book = epub.read_epub(file_path)
            for item in book.get_items():
                if item.get_type() == 9:  # ITEM_DOCUMENT
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text += soup.get_text() + "\n"
        except Exception as e:
            print(f"Ошибка чтения EPUB {file_path}: {e}")
            return ""
        return text
    
    def extract_from_fb2(self, file_path):
        """Извлечение из FB2"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'xml')
            return soup.get_text()
        except Exception as e:
            print(f"Ошибка чтения FB2 {file_path}: {e}")
            return ""
    
    def extract(self, file_path):
        """Основной метод извлечения"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        ext = file_path.suffix.lower()
        
        # Выбор метода по расширению
        if ext == '.txt':
            text = self.extract_from_txt(file_path)
        elif ext == '.pdf':
            text = self.extract_from_pdf(file_path)
        elif ext == '.epub':
            text = self.extract_from_epub(file_path)
        elif ext == '.fb2':
            text = self.extract_from_fb2(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат: {ext}")
        
        if not text:
            raise ValueError(f"Не удалось извлечь текст из {file_path}")
        
        # Очистка текста
        text = self.clean_text(text)
        
        # Сохранение результата
        output_file = self.extracted_dir / f"{file_path.stem}_extracted.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return output_file
    
    def clean_text(self, text):
        """Очистка текста от лишних пробелов и символов"""
        # Замена множественных переносов строк
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Удаление лишних пробелов
        text = re.sub(r' +', ' ', text)
        # Удаление пустых строк в начале и конце
        return text.strip()
    
    def get_extracted_files(self):
        """Получить список извлечённых файлов"""
        return list(self.extracted_dir.glob("*.txt"))