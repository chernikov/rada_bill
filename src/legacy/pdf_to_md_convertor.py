#---------------------------------------------------------------------------------------------
#-- Скрипт для конвертації PDF-файлів у формат Markdown (.md) за допомогою pdfplumber.
#-- Встановлення залежностей: pip install pdfplumber markdownify
#---------------------------------------------------------------------------------------------
import pdfplumber
import os
import argparse
import re
import glob # ДОДАНО: Для рекурсивного пошуку файлів
from markdownify import markdownify as md

def extract_text_with_layout(pdf_path):
    """
    Витягує текст з PDF, намагаючись зберегти базову структуру та абзаци.
    
    Використовує pdfplumber для постранічної обробки та намагається 
    зберегти відступи для імітації базового форматування.
    """
    all_text = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                
                # Заголовок сторінки Markdown
                all_text.append(f"\n# Сторінка {i + 1}\n\n")
                
                # Використовуємо extract_text з layout=True, щоб отримати 
                # більш чистий текст, орієнтований на стовпці та відступи
                page_text = page.extract_text(layout=True)
                
                if page_text:
                    # Очищаємо поширені проблеми: зайві переноси рядків та пробіли
                    # Замінюємо кілька переносів рядків на подвійний перенос (новий абзац)
                    page_text = re.sub(r'(\n\s*){2,}', '\n\n', page_text) 
                    
                    all_text.append(page_text)
                else:
                    all_text.append(" [Текст на цій сторінці не вдалося витягти] \n")
                    
        return "\n".join(all_text)
        
    except FileNotFoundError:
        print(f"❌ Помилка: Файл не знайдено за шляхом: {pdf_path}")
        return None
    except Exception as e:
        print(f"❌ Непередбачувана помилка при читанні PDF: {e}")
        return None


def convert_pdf_to_markdown(pdf_path, output_dir=None):
    """
    Основна функція для конвертації PDF у файл Markdown.
    """
    
    # 1. Визначення шляхів
    input_filename = os.path.basename(pdf_path)
    base_name = os.path.splitext(input_filename)[0]
    
    if output_dir is None:
        # Збереження у тій самій директорії, що й PDF (режим за замовчуванням)
        output_dir = os.path.dirname(pdf_path) or '.' 
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Використовуємо оригінальну назву, але з розширенням .md
    output_filename = f"{base_name}.md" 
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"🚀 Початок конвертації: {input_filename}")
    
    # 2. Витягнення тексту
    raw_text = extract_text_with_layout(pdf_path)
    
    if raw_text is None:
        return
    
    # 3. Базове форматування Markdown (використовуємо markdownify для уніфікації)
    markdown_content = md(raw_text, heading_style="ATX") 
    
    # Додаткова очистка для кращого вигляду Markdown
    # Видаляємо надлишкові порожні рядки
    markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)

    # 4. Збереження результату
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Успішно збережено: {output_path}")
        
    except Exception as e:
        print(f"❌ Помилка збереження файлу: {e}")


def parse_arguments():
    """Обробка аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        description="Конвертує один або кілька PDF-файлів у формат Markdown (.md).",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'input_paths',
        nargs='*',  # Змінено на '*' (нуль або більше)
        help="Шлях(и) до PDF-файлу або папки для сканування. Якщо не вказано, сканує 'data/' рекурсивно."
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default=None,
        help="Опціональна папка для збереження результатів. За замовчуванням: та ж папка, що й PDF."
    )

    args = parser.parse_args()
    return args

if __name__ == "__main__":
    
    args = parse_arguments()
    files_to_process = []
    
    # Обробка вхідних шляхів (файли або папки)
    if not args.input_paths:
        print("🔍 Режим: Аргументи не вказано. Рекурсивний пошук PDF у папці 'data/'...")
        # Використовуємо glob для рекурсивного пошуку всіх PDF у data/
        search_pattern = 'data/**/*.pdf' 
        files_to_process = glob.glob(search_pattern, recursive=True)
        
    else:
        # Логіка обробки наданих аргументів (якщо вони є)
        for path in args.input_paths:
            if os.path.isdir(path):
                # Якщо це папка, шукаємо всі PDF-файли в ній
                for file in os.listdir(path):
                    if file.lower().endswith('.pdf'):
                        files_to_process.append(os.path.join(path, file))
            elif os.path.isfile(path) and path.lower().endswith('.pdf'):
                # Якщо це єдиний PDF-файл
                files_to_process.append(path)
            else:
                print(f"⚠️ Пропущено: Шлях '{path}' не є PDF-файлом або папкою з PDF.")


    if not files_to_process:
        print("🛑 Не знайдено PDF-файлів для обробки. Переконайтеся, що вони існують у 'data/'")
        exit(0)
        
    print(f"\n✅ Знайдено {len(files_to_process)} PDF-файлів для конвертації.")
    
    for pdf_file in files_to_process:
        # Зберігаємо файл у тій самій директорії, якщо -o не вказано
        convert_pdf_to_markdown(pdf_file, args.output_dir)

    print("\n" + "=" * 50)
    print("🎉 Конвертація завершена.")
    print("========================================")