import json
import time
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os

# ==== 1. Парсинг курса с сайта ====
def get_usdt_rate():
    try:
        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver = uc.Chrome(options=options)
        driver.get("https://www.google.com/search?q=usdt+rub")

        time.sleep(5)
        rate_element = driver.find_element(By.CSS_SELECTOR, 'span.DFlfde.SwHCTb')
        rate = float(rate_element.text.replace(',', '.'))

        driver.quit()
        return rate

    except Exception as e:
        print(f"Ошибка при парсинге курса: {e}")
        return None

# ==== 2. Обновление Google таблицы ====
def update_google_sheet(rate):
    try:
        json_str = os.getenv("GOOGLE_SECRET_JSON")
        if not json_str:
            raise Exception("Ошибка: переменная окружения GOOGLE_SECRET_JSON не найдена!")

        creds_dict = json.loads(json_str)

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/ВАШ_ID/edit#gid=0").sheet1

        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        sheet.append_row([now, rate])

        print("Обновление Google Таблицы: Успешно")

    except Exception as e:
        print(f"Ошибка при обновлении Google Таблицы: {e}")

# ==== 3. Основной скрипт ====
def main():
    start = time.time()
    rate = get_usdt_rate()

    if rate:
        update_google_sheet(rate)
        print(f"***Данные обновлены***\nКурс: {rate}\nДата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
    else:
        print("Курс не получен, таблица не обновлена.")

    print(f"Время выполнения: {round(time.time() - start, 2)} секунд")

if __name__ == "__main__":
    main()
