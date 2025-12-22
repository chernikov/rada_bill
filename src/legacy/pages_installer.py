#---------------------------------------------------------------------------------------------
#--Скрипт скачує кратки законопроєктів з сайту Верховної Ради України для подальшого аналізу--
#---------------------------------------------------------------------------------------------
import requests
import re
import os
import time
import argparse
from math import ceil

# --- КОНСТАНТИ НАЛАШТУВАННЯ ---

SEARCH_URL = 'https://itd.rada.gov.ua/billinfo/Bills/searchResults'

# Затримки
SEARCH_DELAY = 1.0  # сек.
DOWNLOAD_DELAY = 0.2  # сек.

# Налаштування Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

PER_PAGE = 30  # Глобальна змінна, яку ми змінюємо в __main__

# Базові заголовки
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://itd.rada.gov.ua/billinfo',
}


# --- ФУНКЦІЇ ---

def create_bill_directory(bill_number):
    """
    Створює ієрархію папок data/0000-0999/000-099/0010/
    та повертає шлях до файлу: data/.../0010/0010.html
    """
    try:
        num = int(bill_number)
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

    # Шлях до папки сотень. !!! ДОДАНО ПРЕФІКС 'data' !!!
    base_path = os.path.join('data', thousand_folder, hundred_folder)

    # Створюємо кінцеву папку з номером законопроєкту (наприклад, 0010)
    bill_folder_path = os.path.join(base_path, bill_number)
    
    # Створення всієї структури папок, включаючи 'data/'
    os.makedirs(bill_folder_path, exist_ok=True)

    # Повертаємо шлях до HTML-файлу всередині цієї папки
    return os.path.join(bill_folder_path, f"{bill_number}.html")


def robust_post_request(url, data, headers):
    """Виконує POST-запит з повторними спробами та базовою затримкою."""

    time.sleep(SEARCH_DELAY)  # Затримка між запитами на пошукові сторінки

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, data=data, headers=headers, timeout=15)
            response.raise_for_status()
            return response

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            if attempt < MAX_RETRIES - 1:
                print(f"   ⚠️ Спроба {attempt + 1} невдала: {e}. Очікування {RETRY_DELAY} сек. перед повтором...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"   ❌ Запит сторінки остаточно невдалий після {MAX_RETRIES} спроб.")
                return None
        except requests.exceptions.HTTPError as e:
            print(f"   ❌ HTTP помилка: {e}")
            return None

    return None


def get_bill_links_from_page(page_html):
    """Парсить HTML сторінки пошуку і витягує посилання та номер законопроєкту."""
    # Регулярний вираз для пошуку посилання на картку та номера
    pattern = re.compile(
        r'<a href="(https://itd\.rada\.gov\.ua/billinfo/Bills/Card/\d+)"[^>]*class="link-blue">(\d+)</a>')
    matches = pattern.findall(page_html)

    # Повертаємо список кортежів: [(bill_number, card_url), ...]
    return [(match[1], match[0]) for match in matches]


def download_bill_card(bill_number, card_url):
    """Завантажує вміст сторінки картки законопроєкту та зберігає його."""

    # output_path тепер включає папки data/0000-0999/000-099/0010/0010.html
    output_path = create_bill_directory(bill_number)

    if not output_path:
        return False
    
    # Перевірка на існування файлу: якщо файл вже є, пропускаємо його
    if os.path.exists(output_path):
        print(f"   ℹ️ Картка {bill_number} вже існує. Пропущено.")
        return True # Вважаємо це успішною операцією

    print(f"   -> Завантаження картки {bill_number} з {card_url}")
    time.sleep(DOWNLOAD_DELAY)  # Затримка між завантаженнями карток

    try:
        # Виконуємо GET-запит на сторінку картки
        response = requests.get(card_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        print(f"   ✅ Збережено: {output_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Помилка завантаження картки {bill_number}: {e}")
        return False


def fetch_and_process_page(page_number, bill_list):
    """Отримує сторінку пошуку, парсить посилання та додає їх до списку."""

    print(f"\nЗавантаження сторінки пошуку №{page_number}...")

    data = {
        'BillSearchModel.session': '10',
        'BillSearchModel.registrationNumberCompareOperation': '2',
        'Paging.per_page': str(PER_PAGE),
        'Paging.page': str(page_number)
    }

    response = robust_post_request(SEARCH_URL, data, HEADERS)

    if response is None:
        return False

    links_on_page = get_bill_links_from_page(response.text)

    if not links_on_page:
        print(f"⚠️ На сторінці {page_number} не знайдено посилань. Продовжуємо...")
        return True

    for bill_number, card_url in links_on_page:
        bill_list.append((bill_number, card_url))

    print(f"   + Додано {len(links_on_page)} законопроєктів.")
    return True


# --- ПАРСЕР АРГУМЕНТІВ ---

def parse_arguments():
    """Обробка аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        description="Завантажує картки законопроєктів з сайту Верховної Ради.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '-p', '--page-range',
        type=str,
        help="Діапазон сторінок для скачування у форматі START-END (наприклад, 1-5) або START (наприклад, 10)."
    )
    group.add_argument(
        '--page',
        type=int,
        help="Викачати лише одну конкретну сторінку."
    )
    group.add_argument(
        '-c', '--count',
        type=int,
        help="Кількість законопроєктів (карток), які потрібно скачати, починаючи з першої сторінки. Наприклад, 100."
    )
    # Зарезервований аргумент на майбутнє
    parser.add_argument(
        '--id',
        type=str,
        help="Зарезервовано: (Comming soon) Скачати законопроєкти за списком ID."
    )

    # Додаткові аргументи для налаштування
    parser.add_argument(
        '--per-page',
        type=int,
        default=PER_PAGE,
        choices=[30, 40, 50],
        help=f"Кількість законопроєктів на сторінці пошуку. За замовчуванням: {PER_PAGE}."
    )
    parser.add_argument(
        '--max-bills',
        type=int,
        default=100,
        help="Зарезервовано: Максимальний ліміт для скачування, якщо використовується --page-range."
    )

    args = parser.parse_args()
    return args


# --- ГОЛОВНА ЛОГІКА СКРИПТА ---

if __name__ == "__main__":

    args = parse_arguments()

    # ПЕРЕПРИСВОЮЄМО значення глобальній змінній
    PER_PAGE = args.per_page

    all_bills_to_download = []

    start_page = 1
    end_page = 1
    max_count = 0

    # 1. Визначення діапазону сторінок для завантаження
    if args.page:
        start_page = args.page
        end_page = args.page
    elif args.page_range:
        try:
            if '-' in args.page_range:
                start_str, end_str = args.page_range.split('-')
                start_page = int(start_str)
                end_page = int(end_str)
            else:
                start_page = int(args.page_range)
                end_page = start_page
        except ValueError:
            print("❌ Некоректний формат діапазону сторінок. Використовуйте START-END або START.")
            exit(1)

    elif args.count:
        start_page = 1
        # Визначаємо, скільки сторінок потрібно для заданої кількості
        end_page = ceil(args.count / PER_PAGE)
        max_count = args.count

    if start_page < 1 or end_page < start_page:
        print("❌ Некоректно заданий діапазон сторінок.")
        exit(1)

    print(f"Старт завантаження: Сторінки {start_page} по {end_page}. {PER_PAGE} пр-тів/стор.")
    if max_count > 0:
        print(f"Буде завантажено не більше {max_count} законопроєктів.")

    # 2. Фаза ЗБОРУ ПОСИЛАНЬ

    current_page = start_page
    while current_page <= end_page:
        # Виходимо з циклу, якщо ми вже зібрали необхідну кількість карток (лише для режиму -c/--count)
        if max_count > 0 and len(all_bills_to_download) >= max_count:
            break

        should_continue = fetch_and_process_page(
            current_page,
            all_bills_to_download
        )

        if not should_continue:
            print("🛑 Критична помилка завантаження сторінки. Збір посилань перервано.")
            break

        current_page += 1

    # Обрізаємо список точно до ліміту, якщо використовувався аргумент -c
    if max_count > 0:
        all_bills_to_download = all_bills_to_download[:max_count]

    print("\n" + "=" * 50)
    print(f"🎉 Збір посилань завершено. Всього зібрано: {len(all_bills_to_download)}.")
    print("=" * 50 + "\n")

    # 3. Фаза ЗАВАНТАЖЕННЯ КАРТОК

    success_count = 0

    if all_bills_to_download:
        print("Починаємо завантаження карток законопроєктів:")

        for bill_number, card_url in all_bills_to_download:
            if download_bill_card(bill_number, card_url):
                success_count += 1

    print("\n" + "=" * 50)
    print(f"🚀 Роботу завершено. Успішно завантажено карток: {success_count}/{len(all_bills_to_download)}")
    print("Всі файли збережено у відповідних папках.")
    print("=" * 50)
    