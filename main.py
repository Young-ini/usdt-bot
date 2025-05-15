import os
import json
import time
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === 1. Пути к системному Chromium и chromedriver на Railway ===
CHROME_BINARY_PATH = "/usr/bin/chromium"
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"

# === 2. Google Sheets ===
SPREADSHEET_KEY = "19qZClNIdNVI_TMFC27HhxVVktWx9M-pezafwYRslkP8"
WORKSHEET_NAME  = "COURSE"

def create_gspread_client():
    raw = os.getenv("GOOGLE_SECRET_JSON")
    if not raw:
        raise RuntimeError("Переменная окружения GOOGLE_SECRET_JSON не найдена!")
    creds_dict = json.loads(raw)
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# === 3. Парсинг курса ===
def get_usdt_rub_price():
    options = Options()
    options.binary_location = CHROME_BINARY_PATH
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(CHROME_DRIVER_PATH),
        options=options
    )
    try:
        driver.get("https://www.bybit.com/en/convert/usdt-to-rub/")
        time.sleep(3)  # даём время на JS-рендеринг
        el = driver.find_element("xpath", '//div[@class="card-info-price green"]')
        text = el.text.strip().replace("₽","").replace(",",".")
        return round(float(text), 2)
    finally:
        driver.quit()

# === 4. Обновление Google Sheet ===
def update_sheet(price):
    client = create_gspread_client()
    sheet  = client.open_by_key(SPREADSHEET_KEY).worksheet(WORKSHEET_NAME)
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    sheet.update("B2", price)
    sheet.update("C2", now)
    return now

# === 5. main ===
if __name__=="__main__":
    start = time.time()
    price = get_usdt_rub_price()
    if price is None:
        print("Курс не получен, таблица не обновлена.")
    else:
        ts = update_sheet(price)
        print("***Данные обновлены***")
        print(f"Курс: {price}")
        print(f"Время: {ts}")
    print(f"Время выполнения: {round(time.time()-start,2)} секунд")
