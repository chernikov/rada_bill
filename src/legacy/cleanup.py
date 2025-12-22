#!/usr/bin/env python3
#---------------------------------------------------------------------------------------------
#-- Скрипт для видалення всіх завантажених даних (папка data/)
#-- Використовуйте з обережністю - видаляє ВСІ завантажені файли!
#---------------------------------------------------------------------------------------------
import os
import shutil
import argparse

# Папка з даними (відносно кореня проєкту)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


def get_folder_size(folder_path):
    """Обчислює розмір папки в байтах."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size


def format_size(size_bytes):
    """Форматує розмір у людино-зрозумілий формат."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def count_files(folder_path):
    """Підраховує кількість файлів у папці."""
    file_count = 0
    dir_count = 0
    file_types = {}
    
    for dirpath, dirnames, filenames in os.walk(folder_path):
        dir_count += len(dirnames)
        for f in filenames:
            file_count += 1
            ext = os.path.splitext(f)[1].lower() or 'no_ext'
            file_types[ext] = file_types.get(ext, 0) + 1
    
    return file_count, dir_count, file_types


def print_statistics(data_dir):
    """Виводить статистику по папці data/."""
    if not os.path.exists(data_dir):
        print(f"📁 Папка '{data_dir}' не існує. Нема чого видаляти.")
        return False
    
    file_count, dir_count, file_types = count_files(data_dir)
    total_size = get_folder_size(data_dir)
    
    print("\n" + "=" * 50)
    print("📊 СТАТИСТИКА ПАПКИ DATA/")
    print("=" * 50)
    print(f"📁 Шлях: {data_dir}")
    print(f"📄 Всього файлів: {file_count}")
    print(f"📂 Всього папок: {dir_count}")
    print(f"💾 Загальний розмір: {format_size(total_size)}")
    
    if file_types:
        print("\n📋 Типи файлів:")
        for ext, count in sorted(file_types.items(), key=lambda x: -x[1]):
            print(f"   {ext}: {count}")
    
    print("=" * 50)
    
    return file_count > 0 or dir_count > 0


def cleanup_all(data_dir, force=False):
    """Видаляє всю папку data/."""
    if not os.path.exists(data_dir):
        print(f"📁 Папка '{data_dir}' не існує.")
        return True
    
    if not force:
        print("\n⚠️  УВАГА! Ця операція видалить ВСІ дані з папки data/!")
        confirm = input("❓ Ви впевнені? (y/n): ").strip().lower()
        
        if confirm not in ["y", "yes", "так", "т"]:
            print("❌ Операцію скасовано.")
            return False
    
    try:
        shutil.rmtree(data_dir)
        print(f"✅ Папку '{data_dir}' успішно видалено.")
        return True
    except Exception as e:
        print(f"❌ Помилка видалення: {e}")
        return False


def cleanup_by_type(data_dir, file_types, force=False):
    """Видаляє файли певного типу."""
    if not os.path.exists(data_dir):
        print(f"📁 Папка '{data_dir}' не існує.")
        return True
    
    files_to_delete = []
    
    for dirpath, dirnames, filenames in os.walk(data_dir):
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in file_types:
                files_to_delete.append(os.path.join(dirpath, f))
    
    if not files_to_delete:
        print(f"📄 Файлів типів {file_types} не знайдено.")
        return True
    
    print(f"\n📄 Знайдено {len(files_to_delete)} файлів для видалення:")
    for f in files_to_delete[:10]:
        print(f"   - {f}")
    if len(files_to_delete) > 10:
        print(f"   ... та ще {len(files_to_delete) - 10} файлів")
    
    if not force:
        confirm = input(f"\n❓ Видалити {len(files_to_delete)} файлів? (y/n): ").strip().lower()
        if confirm not in ["y", "yes", "так", "т"]:
            print("❌ Операцію скасовано.")
            return False
    
    deleted_count = 0
    for f in files_to_delete:
        try:
            os.remove(f)
            deleted_count += 1
        except Exception as e:
            print(f"⚠️ Не вдалося видалити {f}: {e}")
    
    print(f"✅ Видалено {deleted_count} файлів.")
    return True


def cleanup_empty_dirs(data_dir):
    """Видаляє порожні папки."""
    if not os.path.exists(data_dir):
        return True
    
    deleted_count = 0
    
    # Проходимо знизу вверх, щоб спочатку видалити вкладені порожні папки
    for dirpath, dirnames, filenames in os.walk(data_dir, topdown=False):
        if dirpath != data_dir and not os.listdir(dirpath):
            try:
                os.rmdir(dirpath)
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ Не вдалося видалити {dirpath}: {e}")
    
    if deleted_count > 0:
        print(f"✅ Видалено {deleted_count} порожніх папок.")
    else:
        print("📁 Порожніх папок не знайдено.")
    
    return True


def parse_arguments():
    """Обробка аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        description="Видаляє завантажені дані з папки data/.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help="Видалити ВСЮ папку data/ з усім вмістом."
    )
    
    parser.add_argument(
        '--html',
        action='store_true',
        help="Видалити тільки HTML файли (картки законопроєктів)."
    )
    
    parser.add_argument(
        '--pdf',
        action='store_true',
        help="Видалити тільки PDF файли."
    )
    
    parser.add_argument(
        '--docx',
        action='store_true',
        help="Видалити тільки DOCX файли."
    )
    
    parser.add_argument(
        '--md',
        action='store_true',
        help="Видалити тільки MD (Markdown) файли."
    )
    
    parser.add_argument(
        '--txt',
        action='store_true',
        help="Видалити тільки TXT файли (результати аналізу)."
    )
    
    parser.add_argument(
        '--empty',
        action='store_true',
        help="Видалити тільки порожні папки."
    )
    
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help="Показати тільки статистику (без видалення)."
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help="Примусове видалення без підтвердження."
    )
    
    return parser.parse_args()


def interactive_menu(data_dir):
    """Інтерактивне меню для вибору дій."""
    print("\n" + "=" * 50)
    print("🗑️  ОЧИЩЕННЯ ДАНИХ")
    print("=" * 50)
    
    if not print_statistics(data_dir):
        return
    
    print("\n📋 ОБЕРІТЬ ДІЮ:")
    print("-" * 40)
    print("  [1] 🗑️  Видалити ВСЕ (папку data/)")
    print("  [2] 📄 Видалити тільки HTML файли")
    print("  [3] 📕 Видалити тільки PDF файли")
    print("  [4] 📘 Видалити тільки DOCX файли")
    print("  [5] 📝 Видалити тільки MD файли")
    print("  [6] 📃 Видалити тільки TXT файли")
    print("  [7] 📁 Видалити порожні папки")
    print("  [0] ❌ Вихід")
    print("-" * 40)
    
    choice = input("\n  Ваш вибір: ").strip()
    
    if choice == "0":
        print("👋 Вихід.")
        return
    elif choice == "1":
        cleanup_all(data_dir)
    elif choice == "2":
        cleanup_by_type(data_dir, ['.html'])
    elif choice == "3":
        cleanup_by_type(data_dir, ['.pdf'])
    elif choice == "4":
        cleanup_by_type(data_dir, ['.docx'])
    elif choice == "5":
        cleanup_by_type(data_dir, ['.md'])
    elif choice == "6":
        cleanup_by_type(data_dir, ['.txt'])
    elif choice == "7":
        cleanup_empty_dirs(data_dir)
    else:
        print("⚠️ Невірний вибір.")


def main():
    """Головна функція."""
    args = parse_arguments()
    
    # Якщо не вказано жодних аргументів - запускаємо інтерактивний режим
    if not any([args.all, args.html, args.pdf, args.docx, args.md, args.txt, args.empty, args.stats]):
        interactive_menu(DATA_DIR)
        return
    
    # Показати статистику
    if args.stats:
        print_statistics(DATA_DIR)
        return
    
    # Виконати очищення за аргументами
    if args.all:
        cleanup_all(DATA_DIR, force=args.force)
    
    file_types = []
    if args.html:
        file_types.append('.html')
    if args.pdf:
        file_types.append('.pdf')
    if args.docx:
        file_types.append('.docx')
    if args.md:
        file_types.append('.md')
    if args.txt:
        file_types.append('.txt')
    
    if file_types:
        cleanup_by_type(DATA_DIR, file_types, force=args.force)
    
    if args.empty:
        cleanup_empty_dirs(DATA_DIR)


if __name__ == "__main__":
    main()
