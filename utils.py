import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import vobject

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

def get_contacts():
    try:
        with open('./saved_data/contacts.json','r') as f:
            contacts=json.load(f)
        if len(contacts)==0:
            return None
        return contacts
    except FileNotFoundError as e:
        return None
    

def extract_vcf_contacts():
    contacts = []
    while True:
        print("Enter your contacts path")
        file_path=input("  >> ")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for vcard in vobject.readComponents(f.read()):
                    if hasattr(vcard, 'fn'):
                        name = vcard.fn.value 
                    else:
                        continue
                    if hasattr(vcard, 'tel'):
                        phones = [tel.value for tel in vcard.tel_list]
                    else:
                        phones= "Unknown"
                    if hasattr(vcard, 'email'):
                        emails = [email.value for email in vcard.email_list]
                    else:
                        emails="unknown"

                    contacts.append({'name':name,'phones':phones,'emails':emails})
            if len(contacts)==0:
                return "Contacts are empty"

            with open('./saved_data/contacts.json','w') as file:
                json.dump(contacts,file,indent=4)
            
            print("Contacts loaded!")
            return f"Contacts extracted from: {os.path.basename(file_path)}"
        except Exception as e:
            print(f"An error occured: {e}")
            print("Try again!")
            continue