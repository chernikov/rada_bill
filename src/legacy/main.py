#!/usr/bin/env python3
#---------------------------------------------------------------------------------------------
#-- Головний скрипт для запуску повного пайплайну обробки законопроєктів
#-- Послідовність: Скачування сторінок → Завантаження документів → Конвертація в MD → AI аналіз
#---------------------------------------------------------------------------------------------
import subprocess
import sys
import os
from dotenv import load_dotenv

# Шлях до директорії скриптів
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Завантаження змінних з .env файлу
load_dotenv(os.path.join(os.path.dirname(SCRIPT_DIR), '.env'))

# Завантажуємо конфігурацію
BILL_ID = os.getenv('BILL_ID', '').strip()

# --- КОНФІГУРАЦІЯ КРОКІВ ---
STEPS = {
    1: {
        "name": "Скачування сторінок (pages_installer.py)",
        "script": "pages_installer.py",
        "description": "Завантажує HTML-картки законопроєктів з сайту ВР"
    },
    2: {
        "name": "Завантаження документів (doc_loader.py)",
        "script": "doc_loader.py",
        "description": "Завантажує PDF/DOCX файли з HTML-карток"
    },
    3: {
        "name": "Конвертація DOCX → MD (docx_to_md_converter.py)",
        "script": "docx_to_md_converter.py",
        "description": "Конвертує DOCX документи у формат Markdown"
    },
    4: {
        "name": "Конвертація PDF → MD (pdf_to_md_convertor.py)",
        "script": "pdf_to_md_convertor.py",
        "description": "Конвертує PDF документи у формат Markdown"
    },
    5: {
        "name": "AI Аналіз (ai_analyzer.py)",
        "script": "ai_analyzer.py",
        "description": "Аналізує документи через Gemini AI"
    }
}


def print_header():
    """Виводить заголовок програми."""
    print("\n" + "=" * 60)
    print("🏛️  СИСТЕМА АНАЛІЗУ ЗАКОНОПРОЄКТІВ ВЕРХОВНОЇ РАДИ")
    print("=" * 60)
    if BILL_ID:
        print(f"📋 Законопроєкт з .env: {BILL_ID}")
        print("=" * 60)


def print_menu():
    """Виводить головне меню."""
    print("\n📋 ГОЛОВНЕ МЕНЮ:")
    print("-" * 40)
    if BILL_ID:
        print(f"  [1] 🚀 Запустити ПОВНИЙ пайплайн для ЗП {BILL_ID}")
    else:
        print("  [1] 🚀 Запустити ПОВНИЙ пайплайн")
    print("  [2] 📄 Скачати сторінки (pages_installer)")
    print("  [3] 📥 Завантажити документи (doc_loader)")
    print("  [4] 📝 Конвертувати DOCX → MD")
    print("  [5] 📝 Конвертувати PDF → MD")
    print("  [6] 🤖 AI Аналіз документів")
    print("  [0] ❌ Вихід")
    print("-" * 40)


def get_pages_installer_params():
    """Отримує параметри для pages_installer.py."""
    print("\n⚙️  Налаштування скачування сторінок:")
    print("  Оберіть режим:")
    print("  [1] Вказати діапазон сторінок (--page-range)")
    print("  [2] Вказати одну сторінку (--page)")
    print("  [3] Вказати кількість законопроєктів (--count)")
    
    mode = input("\n  Ваш вибір (1/2/3): ").strip()
    
    params = []
    
    if mode == "1":
        start = input("  Початкова сторінка: ").strip()
        end = input("  Кінцева сторінка: ").strip()
        params.extend(["--page-range", f"{start}-{end}"])
    elif mode == "2":
        page = input("  Номер сторінки: ").strip()
        params.extend(["--page", page])
    elif mode == "3":
        count = input("  Кількість законопроєктів: ").strip()
        params.extend(["--count", count])
    else:
        print("  ⚠️ Невірний вибір, використовуємо --count 10")
        params.extend(["--count", "10"])
    
    # Додаткові параметри
    per_page = input("  Кількість на сторінку (30/40/50, Enter для 30): ").strip()
    if per_page in ["30", "40", "50"]:
        params.extend(["--per-page", per_page])
    
    return params


def get_doc_loader_params():
    """Отримує параметри для doc_loader.py."""
    print("\n⚙️  Налаштування завантаження документів:")
    print("  Оберіть режим:")
    print("  [1] Завантажити ВСІ документи (--all)")
    print("  [2] Один законопроєкт (--bill-id)")
    print("  [3] Діапазон законопроєктів (--id-range)")
    print("  [4] Діапазон тисяч (--thousand)")
    
    mode = input("\n  Ваш вибір (1/2/3/4): ").strip()
    
    params = []
    
    if mode == "1":
        params.append("--all")
    elif mode == "2":
        bill_id = input("  Номер законопроєкту: ").strip()
        params.extend(["--bill-id", bill_id])
    elif mode == "3":
        start = input("  Початковий номер: ").strip()
        end = input("  Кінцевий номер: ").strip()
        params.extend(["--id-range", f"{start}-{end}"])
    elif mode == "4":
        thousand = input("  Тисяча (0/1000/2000/.../9000): ").strip()
        params.extend(["--thousand", thousand])
    else:
        print("  ⚠️ Невірний вибір, використовуємо --all")
        params.append("--all")
    
    return params


def get_converter_params():
    """Отримує параметри для конверторів."""
    print("\n⚙️  Налаштування конвертації:")
    print("  [1] Конвертувати всі файли з папки data/ (за замовчуванням)")
    print("  [2] Вказати конкретний файл або папку")
    
    mode = input("\n  Ваш вибір (1/2): ").strip()
    
    params = []
    
    if mode == "2":
        path = input("  Шлях до файлу або папки: ").strip()
        if path:
            params.append(path)
    
    output_dir = input("  Папка для збереження (Enter для тієї ж папки): ").strip()
    if output_dir:
        params.extend(["-o", output_dir])
    
    return params


def get_ai_analyzer_params():
    """Отримує параметри для ai_analyzer.py."""
    print("\n⚙️  Налаштування AI аналізу:")
    print("  [1] Автоматично проаналізувати всі MD файли з data/")
    print("  [2] Вибрати файл вручну (GUI)")
    print("  [3] Вказати конкретний файл")
    
    mode = input("\n  Ваш вибір (1/2/3): ").strip()
    
    params = []
    
    if mode == "1":
        params.append("--auto")
    elif mode == "2":
        params.append("--gui")
    elif mode == "3":
        path = input("  Шлях до файлу: ").strip()
        if path:
            params.extend(["--file", path])
    else:
        params.append("--auto")
    
    # Telegram
    send_tg = input("  Відправляти в Telegram? (y/n): ").strip().lower()
    if send_tg in ["y", "yes", "так", "т"]:
        params.append("--telegram")
    
    return params


def run_script(script_name, params=None):
    """Запускає Python-скрипт з параметрами."""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Скрипт не знайдено: {script_path}")
        return False
    
    cmd = [sys.executable, script_path]
    if params:
        cmd.extend(params)
    
    print(f"\n🚀 Запуск: {script_name}")
    print(f"   Команда: {' '.join(cmd)}")
    print("-" * 40)
    
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(SCRIPT_DIR))
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n⚠️ Виконання перервано користувачем")
        return False
    except Exception as e:
        print(f"❌ Помилка виконання: {e}")
        return False


def run_auto_pipeline_for_bill(bill_id):
    """Запускає автоматичний пайплайн для конкретного законопроєкту з підтвердженням Enter."""
    print("\n" + "=" * 60)
    print(f"🚀 АВТОМАТИЧНИЙ ПАЙПЛАЙН ДЛЯ ЗАКОНОПРОЄКТУ {bill_id}")
    print("=" * 60)
    print("ℹ️  Натискайте Enter для переходу до наступного кроку")
    print("=" * 60)
    
    # Крок 1: Скачування HTML-картки напряму
    print("\n" + "-" * 60)
    print(f"📌 КРОК 1/5: Скачування HTML-картки для ЗП {bill_id}")
    print("-" * 60)
    input("⏎ Натисніть Enter для запуску...")
    
    # Завантажуємо картку напряму
    download_bill_card_direct(bill_id)
    
    # Крок 2: Завантаження документів для конкретного ЗП
    print("\n" + "-" * 60)
    print(f"📌 КРОК 2/5: Завантаження документів для ЗП {bill_id}")
    print("-" * 60)
    input("⏎ Натисніть Enter для запуску...")
    run_script("doc_loader.py", ["--bill-id", bill_id])
    
    # Крок 3: Конвертація DOCX → MD
    print("\n" + "-" * 60)
    print("📌 КРОК 3/5: Конвертація DOCX → MD")
    print("-" * 60)
    input("⏎ Натисніть Enter для запуску...")
    run_script("docx_to_md_converter.py")
    
    # Крок 4: Конвертація PDF → MD
    print("\n" + "-" * 60)
    print("📌 КРОК 4/5: Конвертація PDF → MD")
    print("-" * 60)
    input("⏎ Натисніть Enter для запуску...")
    run_script("pdf_to_md_convertor.py")
    
    # Крок 5: AI Аналіз
    print("\n" + "-" * 60)
    print("📌 КРОК 5/5: AI Аналіз документів")
    print("-" * 60)
    input("⏎ Натисніть Enter для запуску...")
    run_script("ai_analyzer.py", ["--auto", "--telegram"])
    
    print("\n" + "=" * 60)
    print(f"✅ ПАЙПЛАЙН ДЛЯ ЗП {bill_id} ЗАВЕРШЕНО")
    print("=" * 60)


def download_bill_card_direct(bill_id):
    """Завантажує HTML-картку законопроєкту напряму з сайту ВР."""
    import requests
    
    # Формуємо URL картки (формат: https://itd.rada.gov.ua/billinfo/Bills/Card/{bill_id})
    # Але насправді потрібен card_id, а не bill_id
    # Тому використаємо пошук по номеру
    
    search_url = 'https://itd.rada.gov.ua/billinfo/Bills/searchResults'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    # Пошук по номеру законопроєкту
    import re
    
    data = {
        'BillSearchModel.session': '10',
        'BillSearchModel.registrationNumber': bill_id,
        'BillSearchModel.registrationNumberCompareOperation': '1',  # Точний збіг
        'Paging.per_page': '30',
        'Paging.page': '1'
    }
    
    print(f"🔍 Пошук законопроєкту {bill_id}...")
    
    try:
        response = requests.post(search_url, data=data, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Парсимо посилання на картку
        pattern = re.compile(
            r'<a href="(https://itd\.rada\.gov\.ua/billinfo/Bills/Card/\d+)"[^>]*class="link-blue">(\d+)</a>')
        matches = pattern.findall(response.text)
        
        if not matches:
            print(f"⚠️ Законопроєкт {bill_id} не знайдено в результатах пошуку")
            return False
        
        # Шукаємо потрібний номер
        card_url = None
        for url, num in matches:
            if num == bill_id or num == bill_id.lstrip('0'):
                card_url = url
                break
        
        if not card_url:
            # Беремо перший результат
            card_url = matches[0][0]
            print(f"ℹ️ Використовуємо найближчий результат: {matches[0][1]}")
        
        print(f"📥 Завантаження картки: {card_url}")
        
        # Завантажуємо картку
        card_response = requests.get(card_url, headers=headers, timeout=15)
        card_response.raise_for_status()
        
        # Створюємо директорію та зберігаємо
        bill_number_str = bill_id.zfill(4) if len(bill_id) < 4 else bill_id
        num = int(bill_id)
        
        thousand_start = (num // 1000) * 1000
        thousand_folder = f"{thousand_start:04d}-{thousand_start + 999:04d}"
        
        hundred_start = (num // 100) * 100
        hundred_folder = f"{hundred_start:03d}-{hundred_start + 99:03d}"
        
        bill_folder = os.path.join(os.path.dirname(SCRIPT_DIR), 'data', thousand_folder, hundred_folder, bill_number_str)
        os.makedirs(bill_folder, exist_ok=True)
        
        output_path = os.path.join(bill_folder, f"{bill_number_str}.html")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(card_response.text)
        
        print(f"✅ Картку збережено: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Помилка завантаження: {e}")
        return False


def run_full_pipeline():
    """Запускає повний пайплайн обробки."""
    # Якщо є BILL_ID в .env - запускаємо автоматичний режим
    if BILL_ID:
        run_auto_pipeline_for_bill(BILL_ID)
        return
    
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК ПОВНОГО ПАЙПЛАЙНУ")
    print("=" * 60)
    
    # Крок 1: Скачування сторінок
    print("\n📌 КРОК 1/5: Скачування сторінок")
    params = get_pages_installer_params()
    if not run_script("pages_installer.py", params):
        if input("\n⚠️ Продовжити? (y/n): ").strip().lower() != "y":
            return
    
    # Крок 2: Завантаження документів
    print("\n📌 КРОК 2/5: Завантаження документів")
    params = get_doc_loader_params()
    if not run_script("doc_loader.py", params):
        if input("\n⚠️ Продовжити? (y/n): ").strip().lower() != "y":
            return
    
    # Крок 3: Конвертація DOCX
    print("\n📌 КРОК 3/5: Конвертація DOCX → MD")
    run_script("docx_to_md_converter.py")
    
    # Крок 4: Конвертація PDF
    print("\n📌 КРОК 4/5: Конвертація PDF → MD")
    run_script("pdf_to_md_convertor.py")
    
    # Крок 5: AI Аналіз
    print("\n📌 КРОК 5/5: AI Аналіз")
    params = get_ai_analyzer_params()
    run_script("ai_analyzer.py", params)
    
    print("\n" + "=" * 60)
    print("✅ ПОВНИЙ ПАЙПЛАЙН ЗАВЕРШЕНО")
    print("=" * 60)


def main():
    """Головна функція програми."""
    print_header()
    
    # Якщо є BILL_ID в .env - запускаємо автоматичний режим без меню
    if BILL_ID:
        run_auto_pipeline_for_bill(BILL_ID)
        return
    
    while True:
        print_menu()
        choice = input("\n  Ваш вибір: ").strip()
        
        if choice == "0":
            print("\n👋 До побачення!")
            break
        
        elif choice == "1":
            run_full_pipeline()
        
        elif choice == "2":
            params = get_pages_installer_params()
            run_script("pages_installer.py", params)
        
        elif choice == "3":
            params = get_doc_loader_params()
            run_script("doc_loader.py", params)
        
        elif choice == "4":
            params = get_converter_params()
            run_script("docx_to_md_converter.py", params)
        
        elif choice == "5":
            params = get_converter_params()
            run_script("pdf_to_md_convertor.py", params)
        
        elif choice == "6":
            params = get_ai_analyzer_params()
            run_script("ai_analyzer.py", params)
        
        else:
            print("⚠️ Невірний вибір. Спробуйте ще раз.")
        
        input("\n⏎ Натисніть Enter для продовження...")


if __name__ == "__main__":
    main()
