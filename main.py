import os, time, datetime, json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_secret_file():
    secret_json = os.getenv("GOOGLE_SECRET_JSON")
    if not secret_json:
        raise Exception("Переменная окружения GOOGLE_SECRET_JSON не найдена!")
    with open("client_secret.json", "w") as f:
        f.write(secret_json)

create_secret_file()

# Параметры
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"
BYBIT_URL = "https://www.bybit.com/en/convert/usdt-to-rub/"

# ===== Google Sheets =====
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SHEET_NAME     = os.environ.get("SHEET_NAME","COURSE")

# Считываем JSON-ключ из переменной окружения
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
scope = [
  "https://spreadsheets.google.com/feeds",
  "https://www.googleapis.com/auth/spreadsheets",
  "https://www.googleapis.com/auth/drive.file",
  "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc    = gspread.authorize(creds)

def get_usdt_rub_price():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.set_capability("pageLoadStrategy", "eager")

    driver = webdriver.Chrome(service=ChromeService(CHROME_DRIVER_PATH), options=opts)
    try:
        driver.get(BYBIT_URL)
        WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.TAG_NAME,"body")))
        el = WebDriverWait(driver,20).until(
            EC.visibility_of_element_located((By.XPATH,'//div[@class="card-info-price green"]'))
        )
        txt = el.text.replace("₽","").replace(",","." )
        return round(float(txt),2)
    finally:
        driver.quit()

def update_sheet(price):
    sht = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    sht.update("B2", price)
    sht.update("C2", now)

if __name__=="__main__":
    start = time.time()
    price = get_usdt_rub_price()
    if price is None:
        print("Failed to fetch price")
    else:
        update_sheet(price)
        print(f"Updated: {price} ₽ at {datetime.datetime.now()} in {time.time()-start:.2f}s")
