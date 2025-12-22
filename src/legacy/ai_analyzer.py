#!/usr/bin/env python3
#---------------------------------------------------------------------------------------------
#-- Скрипт для AI аналізу документів законопроєктів через Gemini
#-- Підтримує: автоматичне сканування папки data/, GUI вибір, та аргументи командного рядка
#---------------------------------------------------------------------------------------------
import os
import re
import glob
import argparse
import requests  # Для відправки в Telegram
from PyPDF2 import PdfReader
from google import genai
import time
from dotenv import load_dotenv

# Завантаження змінних середовища з .env файлу
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# --- КОНСТАНТИ ---
# 1. Ключ Gemini AI
API_KEY = os.getenv("GOOGLE_API_KEY")

# 2. Поля для Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 3. Папка з даними
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# 4. Затримка між запитами до API (секунди)
API_DELAY = 2


# --- ФУНКЦІЇ ЧИТАННЯ ФАЙЛІВ ---

def extract_text_from_pdf(filepath):
    """Відкриває локальний PDF-файл і витягує з нього весь текст."""
    print(f"   📄 Читання PDF: {os.path.basename(filepath)}")

    if not os.path.exists(filepath):
        print(f"   ❌ Помилка: Файл не знайдено: {filepath}")
        return None

    text = ""
    try:
        with open(filepath, "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"   ❌ Помилка обробки PDF: {e}")
        return None


def extract_text_from_md(filepath):
    """Читає текст з Markdown файлу."""
    print(f"   📝 Читання MD: {os.path.basename(filepath)}")

    if not os.path.exists(filepath):
        print(f"   ❌ Помилка: Файл не знайдено: {filepath}")
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"   ❌ Помилка читання MD: {e}")
        return None


def extract_text_from_txt(filepath):
    """Читає текст з TXT файлу."""
    print(f"   📃 Читання TXT: {os.path.basename(filepath)}")

    if not os.path.exists(filepath):
        print(f"   ❌ Помилка: Файл не знайдено: {filepath}")
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"   ❌ Помилка читання TXT: {e}")
        return None


def extract_text_from_file(filepath):
    """Визначає тип файлу та витягує текст."""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(filepath)
    elif ext == '.md':
        return extract_text_from_md(filepath)
    elif ext == '.txt':
        return extract_text_from_txt(filepath)
    else:
        print(f"   ⚠️ Непідтримуваний формат: {ext}")
        return None


# --- ФУНКЦІЇ ПОШУКУ ФАЙЛІВ ---

def find_analyzable_files(data_dir, file_types=None):
    """Шукає файли для аналізу в папці data/."""
    if file_types is None:
        file_types = ['.md', '.pdf', '.txt']
    
    files = []
    
    for ext in file_types:
        pattern = os.path.join(data_dir, '**', f'*{ext}')
        found = glob.glob(pattern, recursive=True)
        files.extend(found)
    
    # Фільтруємо файли аналізу (VISNOVOK_*.txt) - їх не потрібно повторно аналізувати
    files = [f for f in files if not os.path.basename(f).startswith('VISNOVOK_')]
    
    return sorted(files)


def find_unanalyzed_files(data_dir):
    """Шукає файли, які ще не були проаналізовані."""
    all_files = find_analyzable_files(data_dir)
    unanalyzed = []
    
    for filepath in all_files:
        # Перевіряємо, чи існує файл результату аналізу в тій же папці
        dir_path = os.path.dirname(filepath)
        
        # Шукаємо будь-який файл VISNOVOK_* в тій же папці
        analysis_pattern = os.path.join(dir_path, 'VISNOVOK_*.txt')
        existing_analyses = glob.glob(analysis_pattern)
        
        if not existing_analyses:
            unanalyzed.append(filepath)
    
    return unanalyzed


# --- ФУНКЦІЇ AI АНАЛІЗУ ---

def analyze_and_name_with_gemini(text, source_filename=""):
    """Виконує аналіз за розширеним промптом та генерує назву."""
    if not API_KEY or "ВАШ" in API_KEY:
        print("   ❌ Помилка: Не знайдено GOOGLE_API_KEY.")
        return None, "error_api_key.txt"

    try:
        client = genai.Client(api_key=API_KEY)

        # --- ПРОМПТ ДЛЯ ГЛИБОКОГО АНАЛІЗУ ---
        analysis_prompt = (
            f"Проаналізуй наступний законопроєкт (файл: {source_filename}). "
            "Твій висновок має бути коротким, логічним і структурованим за пунктами:"
            "\n1. **Суть:** Коротка суть законопроєкту та його ціль."
            "\n2. **Автор та Репутація:** Яка особа/орган подала ідею закону? Стисла репутаційна довідка про цього автора (позитивна/негативна)."
            "\n3. **Корупційні ризики:** Чи може бути цей закон пов'язаний з корупцією? Поясни, чому (включаючи потенційні лазівки)."
            "\n4. **Вплив на Україну:** Наскільки сильно цей закон може вплинути на економіку/соціальну сферу України (високий, середній, низький) і чому."
            "\n5. **Плюси та Мінуси:** Головні переваги (Плюси) та недоліки (Мінуси)."
            f"\n\n--- ТЕКСТ ЗАКОНОПРОЄКТУ ---\n\n{text[:30000]}"
        )
        print("   🤖 Відправка на аналіз Gemini...")

        analysis_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=analysis_prompt
        )

        # --- ПРОМПТ ДЛЯ ГЕНЕРАЦІЇ НАЗВИ ---
        naming_prompt = (
            "Проаналізуй наданий висновок по законопроєкту. Створи коротку, змістовну назву для файлу. "
            "Назва має бути транслітерацією (українськими літерами латинкою), без пробілів, без спецсимволів. "
            "Почни відповідь ОДРАЗУ з назви файлу без розширення. Не пиши ніяких пояснень."
            f"\n\n--- АНАЛІЗ ---\n\n{analysis_response.text}"
        )

        print("   📝 Генерація назви файлу...")
        naming_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=naming_prompt
        )

        clean_filename = naming_response.text.strip().replace(' ', '_')
        clean_filename = re.sub(r'[^\w\._-]', '', clean_filename).upper()
        clean_filename = f"VISNOVOK_{clean_filename}.txt"

        return analysis_response.text, clean_filename
    except Exception as e:
        print(f"   ❌ Помилка аналізу Gemini: {e}")
        return None, "error_analysis_failed.txt"


def save_review(review_text, output_dir, filename):
    """Зберігає отриманий відгук у текстовий файл."""
    try:
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(review_text)
        print(f"   ✅ Відгук збережено: {output_path}")
        return output_path
    except Exception as e:
        print(f"   ❌ Помилка збереження файлу: {e}")
        return None


def send_telegram_message(text, token, chat_id):
    """Надсилає текстове повідомлення в Telegram-чат."""
    if "ВАШ" in token or "ВАШ" in chat_id:
        print("   ⚠️ Telegram: Необхідно вказати BOT_TOKEN та CHAT_ID.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Обмеження на довжину повідомлення в Telegram — 4096 символів
    if len(text) > 4000:
        message_text = "⚠️ Повідомлення надто довге, відправлено лише початок:\n\n" + text[:4000]
    else:
        message_text = text

    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("   ✅ Результат відправлено в Telegram!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Помилка відправки в Telegram: {e}")
        return False


# --- ФУНКЦІЇ ОБРОБКИ ---

def process_single_file(filepath, send_telegram=False):
    """Обробляє один файл."""
    print(f"\n{'='*50}")
    print(f"📂 Обробка: {filepath}")
    print('='*50)
    
    # 1. Витягуємо текст
    text = extract_text_from_file(filepath)
    
    if not text or len(text) < 50:
        print("   ❌ Недостатньо тексту для аналізу.")
        return False
    
    # 2. Аналізуємо через AI
    review_text, output_filename = analyze_and_name_with_gemini(text, os.path.basename(filepath))
    
    if not review_text or "error" in output_filename.lower():
        print("   ❌ Аналіз не відбувся.")
        return False
    
    # 3. Зберігаємо результат поруч з оригінальним файлом
    output_dir = os.path.dirname(filepath)
    saved_path = save_review(review_text, output_dir, output_filename)
    
    # 4. Відправляємо в Telegram (якщо потрібно)
    if send_telegram and saved_path:
        # Додаємо інформацію про файл до повідомлення
        tg_message = f"📄 *Аналіз:* {os.path.basename(filepath)}\n\n{review_text}"
        send_telegram_message(tg_message, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    return True


def process_auto_mode(send_telegram=False, only_unanalyzed=True):
    """Автоматично обробляє файли з папки data/."""
    print("\n" + "=" * 60)
    print("🤖 АВТОМАТИЧНИЙ РЕЖИМ АНАЛІЗУ")
    print("=" * 60)
    
    if not os.path.exists(DATA_DIR):
        print(f"❌ Папка data/ не знайдена: {DATA_DIR}")
        return
    
    # Знаходимо файли для аналізу
    if only_unanalyzed:
        files = find_unanalyzed_files(DATA_DIR)
        print(f"📄 Знайдено {len(files)} непроаналізованих файлів.")
    else:
        files = find_analyzable_files(DATA_DIR)
        print(f"📄 Знайдено {len(files)} файлів для аналізу.")
    
    if not files:
        print("✅ Всі файли вже проаналізовані або файлів немає.")
        return
    
    # Показуємо список файлів
    print("\n📋 Файли для аналізу:")
    for i, f in enumerate(files[:10], 1):
        print(f"   {i}. {os.path.relpath(f, DATA_DIR)}")
    if len(files) > 10:
        print(f"   ... та ще {len(files) - 10} файлів")
    
    # Підтвердження
    confirm = input(f"\n❓ Проаналізувати {len(files)} файлів? (y/n): ").strip().lower()
    if confirm not in ["y", "yes", "так", "т"]:
        print("❌ Операцію скасовано.")
        return
    
    # Обробка файлів
    success_count = 0
    for i, filepath in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}]")
        
        if process_single_file(filepath, send_telegram):
            success_count += 1
        
        # Затримка між запитами до API
        if i < len(files):
            print(f"   ⏳ Затримка {API_DELAY} сек...")
            time.sleep(API_DELAY)
    
    print("\n" + "=" * 60)
    print(f"✅ АНАЛІЗ ЗАВЕРШЕНО")
    print(f"   Успішно: {success_count}/{len(files)}")
    print("=" * 60)


def process_gui_mode(send_telegram=False):
    """Режим вибору файлу через GUI."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ImportError:
        print("❌ Tkinter не доступний. Використовуйте --file або --auto режим.")
        return
    
    root = tk.Tk()
    root.withdraw()

    filepath = filedialog.askopenfilename(
        title="Виберіть файл для аналізу",
        initialdir=DATA_DIR if os.path.exists(DATA_DIR) else os.getcwd(),
        filetypes=(
            ("Всі підтримувані", "*.pdf *.md *.txt"),
            ("PDF files", "*.pdf"),
            ("Markdown files", "*.md"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        )
    )

    if not filepath:
        print("❌ Вибір файлу скасовано.")
        return

    process_single_file(filepath, send_telegram)


# --- ПАРСЕР АРГУМЕНТІВ ---

def parse_arguments():
    """Обробка аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        description="AI аналіз документів законопроєктів через Gemini.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    mode_group = parser.add_mutually_exclusive_group()
    
    mode_group.add_argument(
        '--auto', '-a',
        action='store_true',
        help="Автоматично проаналізувати всі непроаналізовані файли з папки data/."
    )
    
    mode_group.add_argument(
        '--auto-all',
        action='store_true',
        help="Автоматично проаналізувати ВСІ файли з папки data/ (навіть ті, що вже аналізувались)."
    )
    
    mode_group.add_argument(
        '--gui', '-g',
        action='store_true',
        help="Відкрити діалогове вікно для вибору файлу."
    )
    
    mode_group.add_argument(
        '--file', '-f',
        type=str,
        help="Шлях до конкретного файлу для аналізу."
    )
    
    parser.add_argument(
        '--telegram', '-t',
        action='store_true',
        help="Відправляти результати аналізу в Telegram."
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help="Показати список файлів для аналізу (без виконання аналізу)."
    )

    return parser.parse_args()


# --- ГОЛОВНА ЛОГІКА ---

def main():
    args = parse_arguments()
    
    # Режим списку файлів
    if args.list:
        print("\n📋 ФАЙЛИ ДЛЯ АНАЛІЗУ В ПАПЦІ data/:")
        print("-" * 50)
        
        if not os.path.exists(DATA_DIR):
            print(f"❌ Папка не існує: {DATA_DIR}")
            return
        
        unanalyzed = find_unanalyzed_files(DATA_DIR)
        all_files = find_analyzable_files(DATA_DIR)
        
        print(f"📄 Всього файлів: {len(all_files)}")
        print(f"📄 Непроаналізованих: {len(unanalyzed)}")
        
        if unanalyzed:
            print("\n📝 Непроаналізовані файли:")
            for f in unanalyzed:
                print(f"   - {os.path.relpath(f, DATA_DIR)}")
        return
    
    # Режим автоматичного аналізу
    if args.auto:
        process_auto_mode(send_telegram=args.telegram, only_unanalyzed=True)
        return
    
    if args.auto_all:
        process_auto_mode(send_telegram=args.telegram, only_unanalyzed=False)
        return
    
    # Режим GUI
    if args.gui:
        process_gui_mode(send_telegram=args.telegram)
        return
    
    # Режим конкретного файлу
    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ Файл не знайдено: {args.file}")
            return
        process_single_file(args.file, send_telegram=args.telegram)
        return
    
    # За замовчуванням - інтерактивний режим
    print("\n" + "=" * 50)
    print("🤖 AI АНАЛІЗАТОР ЗАКОНОПРОЄКТІВ")
    print("=" * 50)
    print("\n📋 ОБЕРІТЬ РЕЖИМ:")
    print("  [1] 🔄 Автоматичний аналіз (непроаналізовані файли)")
    print("  [2] 🔄 Автоматичний аналіз (всі файли)")
    print("  [3] 📁 Вибрати файл (GUI)")
    print("  [4] 📋 Показати список файлів")
    print("  [0] ❌ Вихід")
    
    choice = input("\n  Ваш вибір: ").strip()
    
    send_tg = input("  Відправляти в Telegram? (y/n): ").strip().lower() in ["y", "yes", "так", "т"]
    
    if choice == "1":
        process_auto_mode(send_telegram=send_tg, only_unanalyzed=True)
    elif choice == "2":
        process_auto_mode(send_telegram=send_tg, only_unanalyzed=False)
    elif choice == "3":
        process_gui_mode(send_telegram=send_tg)
    elif choice == "4":
        args.list = True
        main()
    elif choice == "0":
        print("👋 До побачення!")
    else:
        print("⚠️ Невірний вибір.")


if __name__ == "__main__":
    main()