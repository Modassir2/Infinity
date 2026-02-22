import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

os.chdir(os.path.dirname(__file__))

WH_SESSION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_data", "wh_session")

def save_history(history):
    with open('./saved_data/history.json', 'w') as f:
        json.dump(history, f, indent=4)

def load_history():
    if os.path.exists('./saved_data/history.json'):
        with open('history.json', 'r') as f:
            return json.load(f)
    return [{'role': 'system', 'content': "You are Infinity."}]

def turnacate_history(history):
    if len(history) > 31:                              
        return [history[0]] + history[-30:]            
    return history

def get_wh_session():
    if os.path.exists(WH_SESSION_PATH) and os.listdir(WH_SESSION_PATH):
        return WH_SESSION_PATH
    return None

def setup_wh_session():

    os.makedirs(WH_SESSION_PATH, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={WH_SESSION_PATH}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--window-size=1200,800")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://web.whatsapp.com")

    print("\n" + "="*50)
    print("  WHATSAPP SETUP — Scan the QR code in Chrome.")
    print("  Once your chats are visible, come back here.")
    print("="*50)
    input("  Press Enter once you are logged in... ")

    driver.quit()
    print("WhatsApp session saved successfully!\n")