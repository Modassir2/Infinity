import datetime
import json
import math
import subprocess
import webbrowser
import psutil
import threading
import requests
import wikipedia
from win11toast import toast
import urllib.parse
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import utils

MEMORY_FILE = "./saved_data/memory.json"

current_user = None

def _load_memory_db():
    try:
        with open(MEMORY_FILE, 'r') as f:
            content = f.read().strip()  
            if not content:
                return {}  
            return json.loads(content)  
    except FileNotFoundError:
        return {}  

def _save_memory_db(db):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(db, f, indent=4)  


def list_users():
    db = _load_memory_db()
    if not db:
        return "No users registered yet."
    return "Registered users: " + ", ".join(db.keys())  

def register_user(name: str):
 
    db = _load_memory_db()
    if name in db:
        return f"User '{name}' already exists." 
    db[name] = ""  
    _save_memory_db(db)
    return f"User '{name}' registered successfully."

def delete_user(name: str):
    db = _load_memory_db()
    if name not in db:
        return f"User '{name}' not found."
    del db[name]
    _save_memory_db(db)
    return f"User '{name}' deleted."

 

def add_memory(text: str):
    db = _load_memory_db()
    if current_user not in db:
        return f"User '{current_user}' not found. Please register first."
    existing = db[current_user]  
    db[current_user] = (existing + "\n" + text).strip()  
    _save_memory_db(db)
    return f"Memory added for {current_user}! Current memory:\n{db[current_user]}"

def remove_memory(text: str):
    db = _load_memory_db()
    if current_user not in db:
        return f"User '{current_user}' not found."
    updated = db[current_user].replace(text, "").strip() 
    db[current_user] = updated
    _save_memory_db(db)
    return f"Memory removed for {current_user}! Current memory:\n{updated}"

def view_memory():
    db = _load_memory_db()
    if current_user not in db:
        return f"User '{current_user}' not found."
    memory = db[current_user].strip()
    return memory if memory else f"No memory saved for {current_user} yet."

def current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str):
    try:
        allowed = {k: getattr(math, k) for k in dir(math)}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

def weather(city: str):
    city=city.lower()
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    geo_response = requests.get(geo_url).json()
    if not geo_response.get("results"):
        return f"{city} not found!"
    latitude=geo_response['results'][0]['latitude']
    longitude=geo_response['results'][0]['longitude']
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    weather_data = requests.get(weather_url).json()
    current = weather_data["current_weather"]
    temp = current["temperature"]
    wind = current["windspeed"]
    wind_dir= current["winddirection"]
    return f"Currently {temp}°C with wind speeds of {wind} km/h towards {wind_dir}."

def open_app(app_name: str):
    APP_MAP = {
        "chrome": "chrome",
        "notepad": "notepad",
        "calculator": "calc",
        "paint": "mspaint",
        "explorer": "explorer",
        "cmd": "cmd",
        "powershell": "powershell",
        "task manager": "taskmgr",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "vscode": "code",
        "vs code": "code",
        "spotify": "spotify",
        "discord": "discord",
        "vlc": "vlc",
    }


    command = APP_MAP.get(app_name.strip().lower(), app_name)
    command = 'start ' + command
    try:
        subprocess.Popen(command, shell=True)
        return f"Opening {app_name}..."
    except Exception as e:
        return f"Could not open '{app_name}': {e}"
    
def open_website(url: str):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    return f"Opened {url} in your browser."

def get_battery_status():
    battery = psutil.sensors_battery()
    if battery is None:
        return "No battery found. This might be a desktop PC."
    percent = battery.percent
    charging = "charging" if battery.power_plugged else "not charging"
    return f"Battery is at {percent:.0f}% and is currently {charging}."

def wiki_search(query: str, sentences: int = 5):           
    try:
        wikipedia.set_lang("en")
        results = wikipedia.search(query, results=3)    
        if not results:
            return f"No Wikipedia results found for '{query}'."
        summary = wikipedia.summary(results[0], sentences=sentences, auto_suggest=False) 
        return f"Wikipedia — {results[0]}:\n{summary}"    
    except wikipedia.exceptions.DisambiguationError as e:
        options = "\n".join(e.options[:8])        
        return f"'{query}' is ambiguous. Did you mean one of these?\n{options}\nSearch again with a more specific term."
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'. Try a different search term."
    except Exception as e:
        return f"Wiki search error: {e}"

def notify(title: str, body: str='', duration: int=0, on_click: str=''): 
    def _send():                                                               
        toast(title, body, scenario='reminder', on_click=on_click if on_click else None)  
    if duration != 0:
        threading.Timer(duration * 60, _send).start()                         
        return f"Reminder set for {duration} minute(s). Will notify: '{title}'"  
    else:
        _send()
        return f"Notification sent: '{title}'"                                 

def open_later(url: str, delay_minutes: int):                                 
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url                                                
    def _open():
        webbrowser.open(url)                                                  
    threading.Timer(delay_minutes * 60, _open).start()                         
    return f"Will open {url} in {delay_minutes} minute(s) silently."
    
def send_email(to: str, subject: str, body: str):
    params = urllib.parse.urlencode({                  
        'view': 'cm',
        'to': to,
        'su': subject,
        'body': body
    })
    url = f"https://mail.google.com/mail/?{params}"    
    webbrowser.open(url)                               
    return f"Opened Gmail compose to '{to}' with subject '{subject}'. The body has been pre-filled."

def send_whatsapp(phone: str, message: str):
    session = utils.get_wh_session()
    if not session:
        return "WhatsApp is not set up. Please ask user to setup infinity by restarting the UI"

    def _send():
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument(f"--user-data-dir={session}")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=chrome_options)
        try:
            phone_clean = phone.replace(" ", "").replace("-", "")
            driver.get(f"https://web.whatsapp.com/send?phone={phone_clean}")
            wait = WebDriverWait(driver, 30)

            time.sleep(8)

            msg_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
            message_box = wait.until(EC.presence_of_element_located((By.XPATH, msg_xpath)))
            message_box.click()
            message_box.send_keys(message + Keys.ENTER)
        except Exception as e:
            return f"An error occured: {e}"
        finally:
            time.sleep(3)
            driver.quit()

    threading.Thread(target=_send).start()
    return f"Sending WhatsApp message to {phone}... it will be delivered in a few seconds."

def search_contacts(name: str):
    if not utils.get_contacts():
        return "Contacts has not been setup, ask user to load contacts or provide phone no. directly"
    contacts=utils.get_contacts()
    results=[]
    for i in contacts:
        cont_name=i['name']
        if name.lower() in cont_name.lower():
            results.append(i)
    return json.dumps(results,indent=4)