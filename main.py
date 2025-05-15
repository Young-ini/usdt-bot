import os
import re
import time
import json
import datetime
import requests

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Константы
BYBIT_URL        = "https://www.bybit.com/en/convert/usdt-to-rub/"
USER_AGENT       = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/112.0.0.0 Safari/537.36"
)

SPREADSHEET_KEY  = "19qZClNIdNVI_TMFC27HhxVVktWx9M-pezafwYRslkP8"
WORKSHEET_NAME   = "COURSE"

# 1) Авторизация в Google Sheets
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

# 2) Парсинг курса через HTTP + regex
def get_usdt_rub_price():
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(BYBIT_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # ищем div.card-info-price green">85,92₽</div>
        m = re.search(r'<div[^>]*class="card-info-price green"[^>]*>([\d,\.]+)₽', html)
        if not m:
            print("Не найден элемент с курсом на странице.")
            return None

        price = m.group(1).replace(",", ".")
        return round(float(price), 2)

    except Exception as e:
        print("Ошибка при парсинге курса:", e)
        return None

# 3) Запись в Google Sheet
def update_google_sheet(price):
    try:
        client = create_gspread_client()
        sheet  = client.open_by_key(SPREADSHEET_KEY).worksheet(WORKSHEET_NAME)
        now    = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        sheet.update("B2", price)
        sheet.update("C2", now)
        return now

    except Exception as e:
        print("Ошибка при обновлении Google Таблицы:", e)
        return None

# 4) Main
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

    print(f"Время выполнения: {round(time.time() - start, 2)} секунд")
