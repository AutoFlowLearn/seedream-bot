import os
import json
import time
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

APP_URL        = os.environ.get("APP_URL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

def send_to_server(bearer, sas):
    if not APP_URL:
        print("❌ APP_URL not set!")
        return
    webhook_url = f"{APP_URL.rstrip('/')}/api/admin/auto-update-seedream"
    payload     = {"bearer_token": bearer, "sas_token": sas}
    headers     = {"Content-Type": "application/json", "X-Cron-Secret": ADMIN_PASSWORD}
    print(f"🌐 Sending tokens to server...")
    try:
        res = requests.post(webhook_url, json=payload, headers=headers, timeout=30)
        print(f"✅ Server Response: {res.status_code}")
    except Exception as e:
        print(f"❌ Webhook Error: {e}")

def system_check():
    print("=" * 50)
    print("🔍 System Check:")
    print(f"Chromium exists: {os.path.exists('/usr/bin/chromium')}")
    print(f"ChromeDriver exists: {os.path.exists('/usr/bin/chromedriver')}")
    try:
        v = subprocess.check_output(['/usr/bin/chromium', '--version']).decode().strip()
        print(f"Chromium: {v}")
    except Exception as e:
        print(f"Chromium error: {e}")
    try:
        v = subprocess.check_output(['/usr/bin/chromedriver', '--version']).decode().strip()
        print(f"ChromeDriver: {v}")
    except Exception as e:
        print(f"ChromeDriver error: {e}")
    print("=" * 50)

def get_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    opts.binary_location = "/usr/bin/chromium"
    service = Service(executable_path="/usr/bin/chromedriver")
    
    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def run_scraper():
    print("🚀 SeeDream Token Extractor Starting...")
    system_check()
    
    driver = get_driver()
    auth_token, sas_token = None, None

    try:
        driver.get("https://pdfsimpli.com/app/image-editor/generate")
        wait = WebDriverWait(driver, 60)
        time.sleep(15)

        try:
            prompt = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "textarea, input[type='text'], #empty-generate-prompt")
            ))
            prompt.send_keys("cinematic cat walking on moon")
            prompt.send_keys(Keys.ENTER)
            print("✅ Prompt submitted")
        except Exception:
            print("⚠️ Prompt not found, continuing...")

        for i in range(20):
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']
                    if log['method'] == 'Network.requestWillBeSent':
                        url = log['params']['request']['url']
                        hdrs = log['params']['request'].get('headers', {})
                        if "Authorization" in hdrs and not auth_token:
                            if hdrs['Authorization'].startswith("Bearer "):
                                auth_token = hdrs['Authorization']
                                print(f"💎 Bearer captured")
                        if ".png?" in url and "prodlegalsimplistorage" in url and not sas_token:
                            sas_token = "?" + url.split(".png?")[1]
                            print(f"💎 SAS captured (len={len(sas_token)})")
                except Exception:
                    continue
            if auth_token and sas_token:
                break
            time.sleep(3)

        if auth_token and sas_token:
            send_to_server(auth_token, sas_token)
        else:
            print(f"❌ Failed: Bearer={'✅' if auth_token else '❌'} SAS={'✅' if sas_token else '❌'}")

    except Exception as e:
        print(f"⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper()
