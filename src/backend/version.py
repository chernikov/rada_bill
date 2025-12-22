"""
Версія додатку
Автоматично оновлюється при релізах
"""

VERSION = "1.0.0"
BUILD_DATE = "2025-12-22"
BUILD_NUMBER = 1


def get_version():
    """Повертає повну інформацію про версію"""
    return {
        "version": VERSION,
        "build_date": BUILD_DATE,
        "build_number": BUILD_NUMBER,
        "full_version": f"{VERSION}.{BUILD_NUMBER}"
    }


def get_version_string():
    """Повертає версію як рядок"""
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M:%S")
    return f"v{VERSION} (build {BUILD_NUMBER}, {BUILD_DATE} {current_time})"


def increment_build():
    """Інкрементує номер білду та оновлює дату"""
    from datetime import datetime
    
    global BUILD_NUMBER, BUILD_DATE
    BUILD_NUMBER += 1
    BUILD_DATE = datetime.now().strftime("%Y-%m-%d")
    
    # Оновлюємо файл
    with open(__file__, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    content = re.sub(r'BUILD_DATE = "[\d-]+"', f'BUILD_DATE = "{BUILD_DATE}"', content)
    content = re.sub(r'BUILD_NUMBER = \d+', f'BUILD_NUMBER = {BUILD_NUMBER}', content)
    
    with open(__file__, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return get_version_string()


if __name__ == "__main__":
    print(get_version_string())
