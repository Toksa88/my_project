from PIL import Image, ImageDraw, ImageFont
import os

def create_polaroid(input_path, output_path, caption=""):
    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"❌ Помилка при відкритті зображення: {e}")
        return

    border = 50
    bottom_border = 250
    photo_size = 900 
    
    frame_width = photo_size + (border * 2)       
    frame_height = photo_size + border + bottom_border 

    # Робимо ідеальний квадрат (Center Crop)
    width, height = img.size
    min_dim = min(width, height)
    
    left = (width - min_dim) / 2
    top = (height - min_dim) / 2
    right = (width + min_dim) / 2
    bottom = (height + min_dim) / 2
    
    img_cropped = img.crop((left, top, right, bottom))
    img_resized = img_cropped.resize((photo_size, photo_size), Image.Resampling.LANCZOS)

    # Створюємо біле полотно і вставляємо фото
    polaroid = Image.new('RGB', (frame_width, frame_height), 'white')
    polaroid.paste(img_resized, (border, border))

    # Додаємо текст
    if caption:
        draw = ImageDraw.Draw(polaroid)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), caption, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (frame_width - text_width) / 2
        text_y = frame_height - bottom_border + (bottom_border - text_height) / 2 - 20 
        
        draw.text((text_x, text_y), caption, fill="black", font=font)

    # Зберігаємо результат
    polaroid.save(output_path, quality=95)
    print(f"✅ Готово! Твій полароїд збережено як: {output_path}")


if __name__ == "__main__":
    print("📸 === Генератор Полароїдів === 📸")
    print("Підказка: Ти можеш просто перетягнути файл фотографії у це вікно!\n")
    
    # Отримуємо шлях від користувача і прибираємо зайві пробіли та лапки
    user_input_path = input("Введи шлях до фотографії: ").strip(' "\'')
    
    # Перевіряємо, чи існує файл
    if not os.path.exists(user_input_path):
        print("Ой, здається, такого файлу не існує. Перевір шлях і спробуй ще раз!")
    else:
        # Запитуємо підпис
        user_caption = input("Введи підпис для фото (або просто натисни Enter, щоб залишити порожнім): ").strip()
        
        # Автоматично генеруємо ім'я для збереженого файлу (наприклад: image.jpg -> image_polaroid.jpg)
        base_name, ext = os.path.splitext(user_input_path)
        output_filename = f"{base_name}_polaroid{ext}"
        
        print("\n⏳ Обробка зображення...")
        create_polaroid(
            input_path=user_input_path, 
            output_path=output_filename, 
            caption=user_caption
        )