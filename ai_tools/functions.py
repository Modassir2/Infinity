import datetime
import json
import math
import os
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
        driver = _make_chrome_driver(session, headless=True)
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


def read_whatsapp_chat(phone: str, count: int = 5):
    import re as _re
    session = utils.get_wh_session()
    if not session:
        return "WhatsApp is not set up."

    driver = _make_chrome_driver(session, headless=True)
    messages = []
    try:
        phone_clean = phone.replace(" ", "").replace("-", "")
        driver.get(f"https://web.whatsapp.com/send?phone={phone_clean}")
        wait = WebDriverWait(driver, 40)

        wait.until(EC.presence_of_element_located((
            By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'
        )))
        time.sleep(4)

        msg_divs = driver.find_elements(By.XPATH, '//div[@data-id]')
        msg_divs = msg_divs[-count:]

        skip_prefixes = ("PDF\n", "Image\n", "Video\n", "Sticker\n",
                         "Audio\n", "Document\n", "GIF\n", "Contact\n",
                         "Voice message\n")

        for div in msg_divs:
            try:
                data_id = div.get_attribute("data-id") or ""
                sender = "You" if data_id.startswith("true") else "Them"

                try:
                    text_el = div.find_element(
                        By.XPATH, './/span[contains(@class,"selectable-text")]'
                    )
                    text = text_el.text.strip()
                except:
                    text = div.text.strip()

                if not text:
                    continue
                lines = text.split("\n")
                if lines and _re.match(r'^\d{1,2}:\d{2}$', lines[-1].strip()):
                    lines = lines[:-1]
                text = " ".join(lines).strip()

                if not text:
                    continue

                if any(text.startswith(p) for p in skip_prefixes):
                    continue

                messages.append({"sender": sender, "text": text})

            except:
                continue

    finally:
        driver.quit()
    return str(messages)


def _make_chrome_driver(session: str, headless: bool = True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f"--user-data-dir={session}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)


def get_unread_whatsapp_chats():
    import re as _re

    session = utils.get_wh_session()
    if not session:
        return "WhatsApp is not set up. Please restart Infinity to log in."

    driver = _make_chrome_driver(session, headless=True)
    unread_chats = []

    try:
        driver.get("https://web.whatsapp.com")
        wait = WebDriverWait(driver, 50)

        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Chat list"]')))
        time.sleep(6) 

   
        chat_items = driver.find_elements(
            By.XPATH,
            '//div[@aria-label="Chat list"]//div[@role="listitem"]'
        )

        for item in chat_items:
            try:
       
                badge = None
                try:
                    badge = item.find_element(
                        By.XPATH,
                        './/span[contains(@aria-label, "unread message")]'
                    )
                except:
                    pass

                if badge is None:
                    continue  

              
                try:
                    aria_lbl = badge.get_attribute("aria-label") or ""
                    unread_count = aria_lbl.split()[0]
                except:
                    unread_count = "?"

           
                try:
                    name_el = item.find_element(By.XPATH, './/span[@dir="auto" and @title]')
                    contact_name = name_el.get_attribute("title") or name_el.text.strip()
                except:
                    contact_name = "Unknown"

                if not contact_name or contact_name == "Unknown":
                    continue

                unread_chats.append({
                    "name": contact_name,
                    "unread": unread_count,
                })

            except Exception:
                continue

        if not unread_chats:

            all_badges = driver.find_elements(
                By.XPATH,
                '//span[contains(@aria-label, "unread message")]'
            )
            for badge in all_badges:
                try:
                    aria_lbl = badge.get_attribute("aria-label") or ""
                    unread_count = aria_lbl.split()[0]
              
                    parent = badge
                    contact_name = "Unknown"
                    for _ in range(8):
                        try:
                            parent = driver.execute_script("return arguments[0].parentElement;", parent)
                            name_els = parent.find_elements(By.XPATH, './/span[@dir="auto" and @title]')
                            if name_els:
                                contact_name = name_els[0].get_attribute("title") or name_els[0].text.strip()
                                if contact_name:
                                    break
                        except:
                            break
                    if contact_name and contact_name != "Unknown":
                        unread_chats.append({"name": contact_name, "unread": unread_count})
                except:
                    continue

        if not unread_chats:
            return "No unread chats found. Your WhatsApp inbox is all caught up!"


        results = []
        for chat in unread_chats:
            name = chat["name"]
            try:
                chat_el = driver.find_element(
                    By.XPATH,
                    f'//div[@aria-label="Chat list"]//span[@title="{name}"]'
                )
                chat_el.click()
                time.sleep(3)

                msg_divs = driver.find_elements(By.XPATH, '//div[@data-id]')
                msg_divs = msg_divs[-15:]

                skip_prefixes = ("PDF\n", "Image\n", "Video\n", "Sticker\n",
                                 "Audio\n", "Document\n", "GIF\n", "Contact\n",
                                 "Voice message\n")

                messages = []
                for div in msg_divs:
                    try:
                        data_id = div.get_attribute("data-id") or ""
                        sender = "You" if data_id.startswith("true") else name
                        try:
                            text_el = div.find_element(
                                By.XPATH, './/span[contains(@class,"selectable-text")]'
                            )
                            text = text_el.text.strip()
                        except:
                            text = div.text.strip()

                        if not text:
                            continue
                        lines = text.split("\n")
                        if lines and _re.match(r'^\d{1,2}:\d{2}$', lines[-1].strip()):
                            lines = lines[:-1]
                        text = " ".join(lines).strip()
                        if not text or any(text.startswith(p) for p in skip_prefixes):
                            continue
                        messages.append(f"{sender}: {text}")
                    except:
                        continue

                results.append({
                    "contact": name,
                    "unread_count": chat["unread"],
                    "messages": messages
                })
            except Exception as e:
                results.append({
                    "contact": name,
                    "unread_count": chat["unread"],
                    "messages": [f"(Could not open chat: {e})"]
                })

    finally:
        driver.quit()

    output_lines = [f"Found {len(results)} unread chat(s):\n"]
    for r in results:
        output_lines.append(f"=== {r['contact']} ({r['unread_count']} unread) ===")
        if r["messages"]:
            output_lines.extend(r["messages"])
        else:
            output_lines.append("(No readable messages)")
        output_lines.append("")

    return "\n".join(output_lines)


def reply_whatsapp_by_name(contact_name: str, message: str):

    session = utils.get_wh_session()
    if not session:
        return "WhatsApp is not set up. Please restart Infinity to log in."

    result_holder = {"result": None}

    def _send():
        driver = _make_chrome_driver(session, headless=True)
        try:
            driver.get("https://web.whatsapp.com")
            wait = WebDriverWait(driver, 45)
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Chat list"]')))
            time.sleep(4)

    
            try:
                chat_el = driver.find_element(
                    By.XPATH,
                    f'//div[@aria-label="Chat list"]//span[@title="{contact_name}"]'
                )
                chat_el.click()
                time.sleep(3)
            except Exception:
        
                search_box = wait.until(EC.presence_of_element_located((
                    By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'
                )))
                search_box.click()
                search_box.send_keys(contact_name)
                time.sleep(2)

                first_result = wait.until(EC.presence_of_element_located((
                    By.XPATH, '//div[@aria-label="Search results."]//div[@role="listitem"][1]'
                )))
                first_result.click()
                time.sleep(3)

            msg_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
            message_box = wait.until(EC.presence_of_element_located((By.XPATH, msg_xpath)))
            message_box.click()
            message_box.send_keys(message + Keys.ENTER)
            time.sleep(3)
            result_holder["result"] = f"Message sent to {contact_name}: \"{message}\""
        except Exception as e:
            result_holder["result"] = f"Failed to send to {contact_name}: {e}"
        finally:
            driver.quit()

    t = threading.Thread(target=_send, daemon=True)
    t.start()
    t.join(timeout=60)

    return result_holder["result"] or f"Sending message to {contact_name}... (timed out waiting for confirmation)"


def search_contacts(name: str):
    if not utils.get_contacts():
        return "Contacts has not been setup, ask user to load contacts or provide phone no. directly"
    contacts = utils.get_contacts()
    name_clean = name.lower().strip()
    results = []
    for c in contacts:
        cont_name = c['name'].lower()
        cont_name_stripped = cont_name.lstrip('~').strip()
        if name_clean in cont_name_stripped or cont_name_stripped in name_clean:
            results.append(c)
    if not results:
        return f"No contacts found matching '{name}'."
    return json.dumps(results, indent=4)

def save_contact(name: str, phone: str, email: str = ""):
    contacts = utils.get_contacts() or []
    for c in contacts:
        if c['name'].lower() == name.lower():
            return f"Contact '{name}' already exists. Delete it first if you want to replace it."
    contacts.append({
        'name': name,
        'phones': [phone],
        'emails': [email] if email else []
    })
    with open('./saved_data/contacts.json', 'w') as f:
        json.dump(contacts, f, indent=4)
    return f"Contact '{name}' saved with number {phone}."

def delete_contact(name: str):
    contacts = utils.get_contacts()
    if not contacts:
        return "No contacts loaded."
    original_len = len(contacts)
    contacts = [c for c in contacts if c['name'].lower() != name.lower()]
    if len(contacts) == original_len:
        return f"No contact named '{name}' found."
    with open('./saved_data/contacts.json', 'w') as f:
        json.dump(contacts, f, indent=4)
    return f"Contact '{name}' deleted."

def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("Current date and time: %A, %d %B %Y — %I:%M:%S %p")

def list_contacts():
    contacts = utils.get_contacts()
    if not contacts:
        return "No contacts loaded."
    lines = [f"{c['name']} — {', '.join(c['phones']) if isinstance(c['phones'], list) else c['phones']}" for c in contacts]
    return f"{len(contacts)} contacts:\n" + "\n".join(lines)

def list_open_windows():                                                    
    try:                                                                      
        import pygetwindow as gw                                              
        windows = gw.getAllTitles()                                           
        titles = [t.strip() for t in windows if t.strip()]                   
        if not titles:                                                        
            return "No open windows found."                                   
        numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))   
        return f"Open windows ({len(titles)}):\n{numbered}"                  
    except Exception as e:                                                    
        return f"Could not list windows: {e}"                                


_screenshot_buffer = {"image": None, "window_title": ""}                    

def capture_screenshot(window_title: str):                                                                                                         
    try:                                                                      
        import pygetwindow as gw                                              
        import ctypes                                                         
        import ctypes.wintypes                                                
        from PIL import Image                                                 

        all_windows = gw.getAllWindows()                                      
        matches = [w for w in all_windows                                     
                   if window_title.lower() in w.title.lower() and w.title.strip()]  
        if not matches:                                                       
            return f"No window found matching '{window_title}'. Use list_open_windows to check exact titles."  

        win = matches[0]                                                      
        hwnd = win._hWnd                                                      

        
        rect = ctypes.wintypes.RECT()                                        
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))        
        width  = rect.right  - rect.left                                     
        height = rect.bottom - rect.top                                      

        if width <= 0 or height <= 0:                                        
            return f"Window '{win.title}' appears minimized. Please restore it first."  

                
        hwndDC   = ctypes.windll.user32.GetWindowDC(hwnd)                   
        mfcDC    = ctypes.windll.gdi32.CreateCompatibleDC(hwndDC)           
        hBitmap  = ctypes.windll.gdi32.CreateCompatibleBitmap(hwndDC, width, height)  
        ctypes.windll.gdi32.SelectObject(mfcDC, hBitmap)                    


        result = ctypes.windll.user32.PrintWindow(hwnd, mfcDC, 0x2)        

        if not result:                                                   
            result = ctypes.windll.user32.PrintWindow(hwnd, mfcDC, 0)      

                       
        bmp_info = ctypes.create_string_buffer(40)                          
        ctypes.windll.gdi32.GetDIBits(                                       
            mfcDC, hBitmap, 0, height, None, bmp_info, 0                    
        )                                                                     
                             
        class BITMAPINFOHEADER(ctypes.Structure):                            
            _fields_ = [("biSize",          ctypes.c_uint32),                
                        ("biWidth",         ctypes.c_int32),                 
                        ("biHeight",        ctypes.c_int32),                 
                        ("biPlanes",        ctypes.c_uint16),                
                        ("biBitCount",      ctypes.c_uint16),                
                        ("biCompression",   ctypes.c_uint32),                
                        ("biSizeImage",     ctypes.c_uint32),                
                        ("biXPelsPerMeter", ctypes.c_int32),                 
                        ("biYPelsPerMeter", ctypes.c_int32),                 
                        ("biClrUsed",       ctypes.c_uint32),                
                        ("biClrImportant",  ctypes.c_uint32)]                

        bmi = BITMAPINFOHEADER()                                             
        bmi.biSize      = ctypes.sizeof(BITMAPINFOHEADER)                   
        bmi.biWidth     = width                                              
        bmi.biHeight    = -height               
        bmi.biPlanes    = 1                                                  
        bmi.biBitCount  = 32                                       
        bmi.biCompression = 0                               

        buf_size = width * height * 4                                        
        buf = ctypes.create_string_buffer(buf_size)                          
        ctypes.windll.gdi32.GetDIBits(                                       
            mfcDC, hBitmap, 0, height,                                       
            buf, ctypes.byref(bmi), 0                                        
        )                                                                     

                                                
        ctypes.windll.gdi32.DeleteObject(hBitmap)                           
        ctypes.windll.gdi32.DeleteDC(mfcDC)                                 
        ctypes.windll.user32.ReleaseDC(hwnd, hwndDC)                        

            
        img = Image.frombuffer("RGBA", (width, height), buf, "raw", "BGRA", 0, 1)  
        img = img.convert("RGB")                                             

        _screenshot_buffer["image"] = img                                    
        _screenshot_buffer["window_title"] = win.title                       

        return f"Screenshot of '{win.title}' captured (no window switch). Now ask the user where to save it."  

    except Exception as e:                                                    
        return f"Capture failed: {e}"                                        

def save_screenshot(save_path: str = ""):                                                                                                        
    img = _screenshot_buffer.get("image")                                    
    win_title = _screenshot_buffer.get("window_title", "window")             

    if img is None:                                                           
        return "No screenshot in buffer. Call capture_screenshot first."     

    try:                                                                      
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")       
        filename = f"screenshot_{timestamp}.png"                             

                                                
        if not save_path or save_path.strip().lower() == "desktop":          
            folder = os.path.join(os.path.expanduser("~"), "Desktop")       
            full_path = os.path.join(folder, filename)                       
        elif os.path.isdir(save_path) or save_path.endswith(("/", "\\")):   
            folder = save_path.rstrip("/\\")                               
            full_path = os.path.join(folder, filename)                       
        else:                                                                  
            full_path = save_path if save_path.lower().endswith(".png") else save_path + ".png"  
            folder = os.path.dirname(os.path.abspath(full_path))             

        os.makedirs(folder, exist_ok=True)                                   
        img.save(full_path)                                                  

        _screenshot_buffer["image"] = None                                   
        return f"Screenshot of '{win_title}' saved to: {full_path}"        

    except Exception as e:                                                    
        return f"Save failed: {e}"                                           