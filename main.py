import time
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# ========== Настройки Selenium ==========
def get_usdt_rate():
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        driver.get("https://www.google.com/search?q=usdt+rub")
        time.sleep(2)

        rate_element = driver.find_element("xpath", "//span[@class='DFlfde SwHCTb']")
        rate = rate_element.text.replace(',', '.')
        driver.quit()
        return float(rate)

    except Exception as e:
        print("Ошибка при парсинге курса:", e)
        return None

# ========== Обновление Google Таблицы ==========
def update_google_sheet(rate):
    try:
        secret_json = json.loads(os.environ['GOOGLE_SECRET_JSON'])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_json, scope)
        client = gspread.authorize(creds)

        sheet = client.open("USDT_RUB_Rate").sheet1
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        sheet.append_row([now, rate])

        print(f"Google Таблица обновлена: {now} — {rate}")
    except Exception as e:
        print("Ошибка при обновлении Google Таблицы:", e)

# ========== Основной запуск ==========
def main():
    start = time.time()
    rate = get_usdt_rate()

    if rate:
        update_google_sheet(rate)
    else:
        print("Курс не получен, таблица не обновлена.")

    print(f"Время выполнения: {round(time.time() - start, 2)} секунд")

if __name__ == "__main__":
    main()
