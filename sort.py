import shutil
from pathlib import Path

# --- НАЛАШТУВАННЯ ---
# Path.home() автоматично знайде шлях до твоєї домашньої папки (напр. C:\Users\ТвоєІм'я)
DOWNLOADS_DIR = Path.home() / "Downloads"

# Словник категорій. Ти можеш легко додавати сюди нові папки та розширення!
CATEGORIES = {
    "Фото": ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp', '.webp'],
    "Документи": ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
    "Програми": ['.exe', '.msi'],
    "Архіви": ['.zip', '.rar', '.7z', '.tar', '.gz'],
    "Відео": ['.mp4', '.avi', '.mkv', '.mov'],
    "Музика": ['.mp3', '.wav', '.ogg']
}
# --------------------

def get_unique_filepath(target_dir: Path, filename: str) -> Path:
    """
    Перевіряє, чи існує файл. Якщо так, додає цифру до назви (напр. ім'я(1).pdf).
    """
    file_path = target_dir / filename
    
    # Якщо такого файлу ще немає, просто повертаємо шлях
    if not file_path.exists():
        return file_path
    
    # Якщо файл існує, розділяємо його на ім'я та розширення
    stem = file_path.stem      # Назва без розширення (напр. 'документ')
    suffix = file_path.suffix  # Розширення (напр. '.pdf')
    counter = 1
    
    # Шукаємо вільне ім'я, збільшуючи лічильник
    while True:
        new_name = f"{stem}({counter}){suffix}"
        new_path = target_dir / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def sort_files():
    """Основний процес сортування."""
    print(f"Починаємо наводити лад у: {DOWNLOADS_DIR}")
    
    # Перевіряємо, чи взагалі існує папка завантажень
    if not DOWNLOADS_DIR.exists():
        print("Папку завантажень не знайдено!")
        return

    # Перебираємо всі елементи в папці
    for item in DOWNLOADS_DIR.iterdir():
        # Нас цікавлять лише файли, папки не чіпаємо
        if item.is_dir():
            continue
        
        file_extension = item.suffix.lower()
        target_folder_name = "Інше" # Сюди полетить все, що не підійшло під категорії
        
        # Визначаємо, до якої категорії належить розширення файлу
        for folder_name, extensions in CATEGORIES.items():
            if file_extension in extensions:
                target_folder_name = folder_name
                break
        
        # Формуємо шлях до папки призначення (наприклад, Завантаження/Фото)
        target_dir = DOWNLOADS_DIR / target_folder_name
        
        # Створюємо папку призначення, якщо її ще не існує
        target_dir.mkdir(exist_ok=True)
        
        # Отримуємо безпечне ім'я файлу (з цифрою, якщо треба)
        new_file_path = get_unique_filepath(target_dir, item.name)
        
        # Переміщуємо файл
        try:
            shutil.move(str(item), str(new_file_path))
            print(f"✅ Переміщено: {item.name} -> {target_folder_name}/{new_file_path.name}")
        except Exception as e:
            print(f"❌ Помилка при переміщенні {item.name}: {e}")

if __name__ == "__main__":
    sort_files()
    print("🎉 Прибирання успішно завершено!")