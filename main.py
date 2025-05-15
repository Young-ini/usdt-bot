from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import datetime
import time

BYBIT_URL = "https://www.bybit.com/en/convert/usdt-to-rub/"

# Авторизация в Google Sheets через переменную окружения
def authenticate_google_sheets():
    google_secret = os.getenv('GOOGLE_SECRET_JSON')
    if not google_secret:
        raise Exception("Ошибка: переменная окружения GOOGLE_SECRET_JSON не найдена!")

    credentials_dict = json.loads(google_secret)
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# Получение курса USDT-RUB с Bybit
def get_usdt_rub_price(headless=True):
    driver = None
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        )
        chrome_options.set_capability("pageLoadStrategy", "eager")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(BYBIT_URL)

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        price_element = wait.until(
            EC.visibility_of_element_located((By.XPATH, '//div[@class="card-info-price green"]'))
        )

        price_text = price_element.text.strip()
        price = price_text.replace("₽", "").replace(",", ".").strip()
        return round(float(price), 2)

    except Exception as e:
        print(f"Ошибка при парсинге курса: {e}")
        return None

    finally:
        if driver:
            driver.quit()

# Обновление Google Таблицы
def update_google_sheet(price):
    try:
        client = authenticate_google_sheets()

        sheet = client.open_by_key("19qZClNIdNVI_TMFC27HhxVVktWx9M-pezafwYRslkP8").worksheet("COURSE")
        sheet.update_cell(2, 2, price)
        current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        sheet.update_cell(2, 3, current_time)

        print(f"✅ Данные обновлены: Курс {price}, Время {current_time}")
        return True

    except Exception as e:
        print(f"Ошибка при обновлении Google Таблицы: {e}")
        return False

# Основной блок запуска
if __name__ == "__main__":
    start_time = time.time()
    price = get_usdt_rub_price()

    if price:
        success = update_google_sheet(price)
        elapsed = round(time.time() - start_time, 2)
        print(f"***Данные обновлены***")
        print(f"Курс: {price}")
        print(f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
        print(f"Обновление Google Таблицы: {'Успешно' if success else 'Не удалось'}")
        print(f"Время выполнения: {elapsed} секунд")
    else:
        print("Курс не получен, таблица не обновлена.")
