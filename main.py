import os
import re
import time
import json
import datetime
import requests

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Константы ===
BYBIT_URL        = "https://www.bybit.com/en/convert/usdt-to-rub/"
SPREADSHEET_KEY  = "19qZClNIdNVI_TMFC27HhxVVktWx9M-pezafwYRslkP8"
WORKSHEET_NAME   = "COURSE"
USER_AGENT       = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                   "AppleWebKit/537.36 (KHTML, like Gecko) " \
                   "Chrome/112.0.0.0 Safari/537.36"

# === Google Sheets ===
def create_gspread_client():
    raw = os.getenv("GOOGLE_SECRET_JSON")
    if not raw:
        raise RuntimeError("Переменная GOOGLE_SECRET_JSON не найдена!")
    creds_dict = json.loads(raw)
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# === Парсинг курса ===
def get_usdt_rub_price():
    try:
        headers = {"User-Agent": USER_AGENT}
        r = requests.get(BYBIT_URL, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text
        # Ищем <div class="card-info-price green">85,92₽</div>
        m = re.search(r'<div[^>]+class="card-info-price green"[^>]*>([\d,\.]+)₽', html)
        if not m:
            print("Не нашли элемент с курсом на странице.")
            return None
        price = m.group(1).replace(",", ".")
        return round(float(price), 2)
    except Exception as e:
        print("Ошибка при парсинге курса:", e)
        return None

# === Обновление Google Sheet ===
def update_google_sheet(price):
    try:
        client = create_gspread_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(WORKSHEET_NAME)
        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        sheet.update("B2", price)
        sheet.update("C2", now)
        return now
    except Exception as e:
        print("Ошибка при обновлении Google Таблицы:", e)
        return None

# === Main ===
if __name__ == "__main__":
    start = time.time()

    price = get_usdt_rub_price()
    if price is None:
        print("Курс не получен, таблица не обновлена.")
    else:
        ts = update_google_sheet(price)
        if ts:
            print("***Данные обновлены***")
            print(f"Курс: {price}")
            print(f"Время: {ts}")
        else:
            print("Таблица не обновлена.")

    print(f"Время выполнения: {round(time.time()-start, 2)} секунд")
