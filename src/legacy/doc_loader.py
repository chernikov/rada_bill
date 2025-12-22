#------------------------------------------------------------------------------------------------
#--Скрипт який викачує документи (.pdf/.docx) з раніше завантажених HTML-карток законопроєктів.--
#------------------------------------------------------------------------------------------------
import requests
import re
import os
import time
import glob
import argparse

# --- КОНСТАНТИ НАЛАШТУВАННЯ ---

DOWNLOAD_URL = 'https://itd.rada.gov.ua/billinfo/api/file/download/'
DOWNLOAD_DELAY = 0.5  # сек.

# Заголовки для завантаження файлів
DOWNLOAD_HEADERS = {
    'accept': '*/*',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'x-current-chunk': '0',
    # !!! КРИТИЧНО ВАЖЛИВО: Вихідний Cookie повернуто.
    # Якщо завантаження не працюватиме, замініть цей рядок на актуальний Cookie
    # з вашого браузера (наприклад, використовуючи Інструменти розробника -> Мережа -> Заголовок запиту)
    'Cookie': 'sid=a2e5a4963-13a5-48b4-8116-a36942321854; api=c70996c2-ad94-4e59-8879-482127b84631; _gid=GA1.3.376696580.1758866819; _ga=GA1.1.956331489.1758262344; _ga_R9WGJW46EG=GS2.1.s1758866819$o2$g1$t1758868164$j58$l0$h0'
}


# --- ФУНКЦІЇ СТРУКТУРИ ПАПОК (ДЛЯ ПОШУКУ) ---

def generate_bill_path(bill_number):
    """
    Генерує очікуваний шлях до HTML-файлу картки.
    Повертає відносний шлях: data/0000-0999/000-099/0010/0010.html
    """
    try:
        num = int(bill_number)
        bill_number_str = f"{num:04d}"
    except ValueError:
        return None

    # Папка тисяч: 0000-0999
    thousand_start = (num // 1000) * 1000
    thousand_end = thousand_start + 1000
    thousand_folder = f"{thousand_start:04d}-{thousand_end - 1:04d}"

    # Папка сотень: 000-099
    hundred_start = (num // 100) * 100
    hundred_end = hundred_start + 100
    hundred_folder = f"{hundred_start:03d}-{hundred_end - 1:03d}"

    # Базовий шлях: 0000-0999/000-099/0010/
    bill_folder_path = os.path.join(thousand_folder, hundred_folder, bill_number_str)
    
    # !!! ДОДАНО ПРЕФІКС data/ !!!
    full_path = os.path.join('data', bill_folder_path, f"{bill_number_str}.html")

    return full_path


# --- ФУНКЦІЇ ПАРСИНГУ ТА ЗАВАНТАЖЕННЯ ---

def get_file_metadata_from_card(html_content):
    """
    Парсить HTML-картку та витягує ID та розширення файлів (.pdf, .docx).
    """
    pattern = re.compile(
        r'<a[^>]*class="downloadFile"[^>]*'
        r'data-id="(?P<id>\d+)"[^>]*'
        r'data-ext="(?P<ext>\.\w+)"[^>]*'
        r'data-file-name="(?P<name>[^"]+)"[^>]*>'
    )
    
    metadata_list = []
    
    for match in pattern.finditer(html_content):
        ext = match.group('ext').lower()
        if ext in ('.pdf', '.docx'):
            metadata_list.append({
                'id': match.group('id'),
                'ext': ext,
                'name': match.group('name')
            })
            
    return metadata_list


def download_bill_file(file_id, output_path, output_filename):
    """Виконує HTTP-запит з динамічним заголовком x-file-id та зберігає файл."""
    
    full_output_path = os.path.join(output_path, output_filename)
    
    # ПЕРЕВІРКА: Пропускаємо, якщо файл вже існує
    if os.path.exists(full_output_path):
        print(f"   ℹ️ Документ {output_filename} вже існує. Пропущено.")
        return True
        
    print(f"   -> Завантаження ID {file_id}: {output_filename}")
    
    headers = DOWNLOAD_HEADERS.copy()
    headers['x-file-id'] = file_id
    
    time.sleep(DOWNLOAD_DELAY) 

    try:
        response = requests.get(DOWNLOAD_URL, headers=headers, stream=True, timeout=30)
        response.raise_for_status() 

        if response.content:
            # Створення папки (наприклад, data/0000/000/0010), якщо вона не існує
            os.makedirs(output_path, exist_ok=True)
            
            with open(full_output_path, 'wb') as f:
                f.write(response.content)

            print(f"   ✅ Збережено документ: {full_output_path}")
            return True
        else:
            print(f"   ❌ Помилка ID {file_id}: Вміст файлу порожній.")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Помилка завантаження ID {file_id}: {e}")
        return False


def process_downloaded_card(card_file_path):
    """Парсить завантажену картку та скачує документи поруч з нею."""
    
    bill_number = os.path.splitext(os.path.basename(card_file_path))[0]
    
    if not re.match(r'\d{4}', bill_number):
        print(f"⚠️ Пропущено: Некоректна назва файлу ({card_file_path}). Очікується NNNN.html.")
        return 0

    print(f"\n===== Обробка документів для ЗП {bill_number} =====")
    
    # 1. Читання вмісту HTML-картки
    try:
        with open(card_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"❌ Файл картки не знайдено: {card_file_path}")
        return 0
    
    # 2. Витягнення метаданих файлів
    file_metadata = get_file_metadata_from_card(html_content)
    
    if not file_metadata:
        print("ℹ️ На картці не знайдено посилань на файли .pdf або .docx.")
        return 0

    print(f"Знайдено {len(file_metadata)} файлів для завантаження.")
    
    # 3. Цільова папка (директорія HTML-файлу, наприклад, data/0000-0999/000-099/0010)
    output_path = os.path.dirname(card_file_path)

    # 4. Завантаження кожного файлу
    download_count = 0
    for i, meta in enumerate(file_metadata, 1):
        file_id = meta['id']
        file_ext = meta['ext']
        
        # Назва файлу: [0010_ID_порядковий_номер.ext]
        output_filename = f"{bill_number}_{file_id}_{i}{file_ext}" 
        
        if download_bill_file(file_id, output_path, output_filename):
            download_count += 1

    print(f"===== Обробка документів {bill_number} завершена. Завантажено {download_count} файлів. =====")
    return download_count


# --- ПАРСЕР АРГУМЕНТІВ ---

def parse_arguments():
    """Обробка аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        description="Скачує документи (.pdf/.docx) з раніше завантажених HTML-карток законопроєктів.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument(
        '--bill-id',
        type=int,
        help="Завантажити документи для одного конкретного законопроєкту за його номером (наприклад, 10)."
    )
    group.add_argument(
        '--id-range',
        type=str,
        help="Завантажити документи для діапазону номерів ЗП у форматі START-END (наприклад, 100-199)."
    )
    group.add_argument(
        '--thousand',
        type=int,
        choices=[0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000],
        help="Завантажити документи для всіх ЗП у конкретному діапазоні тисяч (наприклад, 2000 для 2000-2999)."
    )
    group.add_argument(
        '--from-file',
        type=str,
        help="Шлях до текстового файлу, що містить номери законопроєктів (один номер на рядок)."
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help="Завантажити документи для ВСІХ знайдених HTML-карток. (Використовується за замовчуванням)"
    )

    args = parser.parse_args()
    return args

# --- ЛОГІКА ПОШУКУ ФАЙЛІВ ---

def get_bill_numbers_from_args(args):
    """Визначає список номерів законопроєктів на основі наданих аргументів."""
    bill_numbers = set()

    if args.bill_id:
        bill_numbers.add(args.bill_id)
    
    elif args.id_range:
        try:
            start, end = map(int, args.id_range.split('-'))
            if start > end:
                start, end = end, start 
            bill_numbers.update(range(start, end + 1))
        except ValueError:
            print("❌ Некоректний формат діапазону. Використовуйте START-END (наприклад, 100-199).")
            return None
    
    elif args.thousand is not None:
        start = args.thousand
        end = args.thousand + 999
        bill_numbers.update(range(start, end + 1))

    elif args.from_file:
        try:
            with open(args.from_file, 'r') as f:
                for line in f:
                    try:
                        num = int(line.strip())
                        bill_numbers.add(num)
                    except ValueError:
                        print(f"⚠️ Пропущено некоректний номер у файлі: {line.strip()}")
        except FileNotFoundError:
            print(f"❌ Файл не знайдено: {args.from_file}")
            return None
            
    return sorted([f"{num:04d}" for num in bill_numbers])


# --- ГОЛОВНА ЛОГІКА СКРИПТА ---

if __name__ == "__main__":
    
    args = parse_arguments()
    all_card_files_to_process = []
    
    # 1. Визначення цільових файлів
    if args.all or (not any([args.bill_id, args.id_range, args.thousand, args.from_file])):
        print("🔍 Режим: Обробка ВСІХ знайдених HTML-карток у директорії 'data/'.")
        # Пошук у 'data/' та всіх її підпапках
        search_pattern = 'data/**/*.html' 
        
        # Фільтруємо, щоб обробляти лише файли NNNN.html
        all_card_files_to_process = [f for f in glob.glob(search_pattern, recursive=True) 
                                     if re.match(r'\d{4}\.html$', os.path.basename(f))]
        
    else:
        # Режим "ВИБІРКОВИЙ"
        target_bill_numbers = get_bill_numbers_from_args(args)
        
        if target_bill_numbers is None:
            exit(1)
            
        print(f"🔍 Режим: Обробка {len(target_bill_numbers)} вибраних законопроєктів.")
        
        for bill_num_str in target_bill_numbers:
            # generate_bill_path вже повертає шлях з префіксом 'data/'
            expected_path = generate_bill_path(bill_num_str) 
            if os.path.exists(expected_path):
                all_card_files_to_process.append(expected_path)
            else:
                print(f"⚠️ Файл картки {bill_num_str}.html не знайдено за очікуваним шляхом: {expected_path}")

    if not all_card_files_to_process:
        print("\n🛑 Не знайдено жодного HTML-файлу для обробки. Переконайтеся, що ви запустили bill_card_downloader.py і всі файли знаходяться у 'data/'.")
        exit(0)

    print(f"✅ Знайдено {len(all_card_files_to_process)} карток для обробки.")

    # 2. Обробка знайдених файлів
    total_downloads = 0
    total_cards_processed = 0
    
    for card_path in all_card_files_to_process:
        total_downloads += process_downloaded_card(card_path)
        total_cards_processed += 1
        
    print("\n" + "=" * 50)
    print(f"🎉 Роботу завершено.")
    print(f"   Оброблені HTML-картки: {total_cards_processed}")
    print(f"   Загалом завантажено документів: {total_downloads}")
    print("========================================")
