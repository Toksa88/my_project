import sys
import os
import time
import requests
import re
import concurrent.futures
import logging  # НОВА БІБЛІОТЕКА ДЛЯ ПРОФЕСІЙНОГО ЛОГУВАННЯ
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- НАЛАШТУВАННЯ ЛОГУВАННЯ ---
# Створюємо базові налаштування: пишемо логи рівня INFO і вище
# Логи йтимуть і в консоль, і у файл 'scraper.log'
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper.log", encoding="utf-8", mode="a"),
        logging.StreamHandler()
    ]
)


def sanitize_filename(name):
    """
    Очищає назву. Якщо назва виходить порожньою (Edge case), 
    використовує таймстемп для уникнення помилок створення папки.
    """
    clean_name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    # Якщо після очищення назва зникла
    if not clean_name:
        fallback_name = f"unknown_product_{int(time.time())}"
        logging.warning(
            f"Назва товару порожня або складалася зі спецсимволів. Використовуємо: {fallback_name}")
        return fallback_name
    return clean_name


def download_single_image(session, img_url, filename):
    """
    Завантажує ОДНЕ фото, використовуючи спільну сесію (requests.Session).
    """
    try:
        # Використовуємо session замість requests
        response = session.get(img_url, timeout=10)
        if len(response.content) >= 10000:
            with open(filename, 'wb') as file:
                file.write(response.content)
            logging.info(f"Збережено: {os.path.basename(filename)}")
            return True
        return False
    except Exception as e:
        logging.error(f"Помилка завантаження {img_url}: {e}")
        return False


def download_prom_gallery_and_info(url, base_folder="prom_products"):
    logging.info(f"Відкриваємо сторінку: {url}")

    # Визначаємо, де лежить програма (працює і для .py, і для .exe)
    if getattr(sys, 'frozen', False):
        # Якщо це скомпільований .exe файл
        script_dir = os.path.dirname(sys.executable)
    else:
        # Якщо це звичайний .py скрипт
        script_dir = os.path.dirname(os.path.abspath(__file__))

    absolute_base_folder = os.path.join(script_dir, base_folder)

    # Налаштування Headless Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    try:
        h1_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        raw_product_name = h1_element.text.strip()
        product_name = sanitize_filename(raw_product_name)
        logging.info(f"Знайдено товар: {product_name}")

    except Exception as e:
        logging.error("Не вдалося знайти назву товару. Перевір посилання.")
        driver.quit()
        return

    product_folder = os.path.join(absolute_base_folder, product_name)
    try:
        if not os.path.exists(product_folder):
            os.makedirs(product_folder)
    except PermissionError:
        logging.error(
            "Windows забороняє створити папку. Перевір права доступу.")
        driver.quit()
        return

    # Збір інформації
    logging.info("Збираємо текстову інформацію...")
    try:
        price = driver.find_element(
            By.CSS_SELECTOR, '[data-qaid="product_price"]').text.strip()
    except:
        price = "Ціну не знайдено"

    try:
        description = driver.find_element(
            By.CSS_SELECTOR, '[data-qaid="product_description"]').text.strip()
    except:
        description = "Опис не знайдено"

    info_file_path = os.path.join(product_folder, f"{product_name}_info.txt")
    with open(info_file_path, "w", encoding="utf-8") as text_file:
        text_file.write(
            f"Назва: {raw_product_name}\nЦіна: {price}\nПосилання: {url}\n\n--- Опис ---\n{description}")

    # Збір посилань на фото
    image_urls = set()
    images = driver.find_elements(By.TAG_NAME, 'img')

    words_in_title = raw_product_name.split()
    keywords = [word.lower() for word in words_in_title[:3]]

    for img in images:
        src = img.get_attribute('src')
        alt = img.get_attribute('alt') or ""

        if src and src.startswith('http') and 'images.prom.ua' in src:
            if not alt or all(kw in alt.lower() for kw in keywords):
                high_res_url = re.sub(r'_w\d+_h\d+', '_w1280_h1280', src)
                image_urls.add(high_res_url)

    logging.info(
        f"Знайдено {len(image_urls)} фотографій. Запускаємо турбо-завантаження!")
    driver.quit()

    # --- СТВОРЮЄМО СЕСІЮ (requests.Session) ---
    # Сесія зберігатиме з'єднання відкритим та використовуватиме заголовки для кожного запиту
    session = requests.Session()

    # Додаємо User-Agent, щоб сервер бачив нас як звичайний браузер
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    # ------------------------------------------

    url_list = list(image_urls)
    downloaded_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for index, img_url in enumerate(url_list):
            filename = os.path.join(
                product_folder, f"{product_name}_{index + 1}.jpg")
            # Передаємо нашу сесію у кожне завдання
            future = executor.submit(
                download_single_image, session, img_url, filename)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                downloaded_count += 1

    logging.info(
        f"Товар '{product_name}' завантажено! (Фотографій: {downloaded_count})")


# --- БЛОК ЗАПУСКУ ---
if __name__ == "__main__":
    print("*" * 60)
    print("⚡ Вітаємо в ПРО-завантажувачі товарів з Prom.ua!")
    print("Логи автоматично записуються у файл scraper.log")
    print("Щоб вийти з програми, просто напиши 'вихід'.")
    print("*" * 60)

    while True:
        target_url = input("\n🔗 Встав посилання на товар: ").strip()

        if target_url.lower() in ['вихід', 'exit', 'quit', 'q', '']:
            logging.info("Роботу завершено користувачем.")
            print("👋 Роботу завершено. Гарного дня!")
            break

        if not target_url.startswith("http"):
            logging.warning(f"Недійсне посилання введено: {target_url}")
            print("⚠️ Це не схоже на дійсне посилання.")
            continue

        start_time = time.time()
        download_prom_gallery_and_info(target_url)
        end_time = time.time()

        logging.info(
            f"Витрачено часу: {round(end_time - start_time, 2)} секунд")
        print("-" * 60)
