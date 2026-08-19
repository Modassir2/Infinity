import pyautogui
import mss
import base64
import time
import utils
import win32gui
import win32con
import cv2
import numpy as np
import base64
import re
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from classes import config,agent

w = config.res_x
h = config.res_y
mon =  config.mon
desktop_copilot_system_prompt = """
You are Desktop Copilot, `desktop_copilot` subagent.
You have been called by the `call_subagent` tool by `main_agent`. Respond to the tool call and complete the task. Follow the instructions given in the `call_subagent` tool.


# PRIORITY RULE:
-. Aknowlege your actions after each step and confirm your actions to the user. Then execute the next step.
-. Follow the work flow order strictly.
-. Follow the steps strictly and ask user if details are vague.
-. Improvise over unexpected steps.
-. Do not submit gmails, payments, bookings etc., only fill in the details and ask the user to continue.
-. The `type_text` tool automatically brings the textbox to focus, you don't need to click on the textboox to bring it to focus.

# WORK FLOW ORDER:
1. Generate clear steps to acomplish the given task marked as Step 1, Step 2... etc.
2. At each step search for a available keyboard shortcut and use it if any revelent shortcuts are returned.
3. Verify if the current step is completed by looking at the screenshot before moving to next step.
4. Improvise/edit or change steps if required or asked by user."""

#HELPER FUNCTIONS
def get_screenshot(mon:int=mon):
    with mss.mss() as screen:
        screen.shot(output="monitor-2.png", mon=mon)
    with open('monitor-2.png','rb') as img:
        base64img=base64.b64encode(img.read()).decode('utf-8')
    return f"data:image/png;base64,{base64img}"

def annonated_cursor(image_url:str=get_screenshot(),coords:list[int,int]=pyautogui.position()):
    image_b64=image_url[22::]
    x,y=coords
    #Decode base64 string to OpenCV image
    img_data = base64.b64decode(image_b64)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    #Crosshair parameters
    color = (0, 0, 255) #Future Moda dont forget -> (BGR not RGB)
    thickness = 2
    size = 12
    #Draw horizontal and vertical lines (+)
    cv2.line(img, (x - size, y), (x + size, y), color, thickness)
    cv2.line(img, (x, y - size), (x, y + size), color, thickness)
    # 4. Re-encode image back to base64
    _, buffer = cv2.imencode('.png', img)
    base64img = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{base64img}"

def _get_open_apps_raw():
    windows = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((title, hwnd))
        return True
    win32gui.EnumWindows(callback, None)
    return windows

def focus_window(app_name):
    current_hwnd = win32gui.GetForegroundWindow() 
    windows = _get_open_apps_raw()
    name_lower = app_name.lower()
    for title, hwnd in windows:
        if name_lower in title.lower():
            if hwnd == current_hwnd:
                return True
            win32gui.SetForegroundWindow(hwnd)
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return True
    return False

def load_BM25Retriever(index_path:str=r".\data\Shortcuts.md",n:int=4):
    with open(index_path, "r") as f:
        raw_lines = f.readlines()
    saved_lines = [line for line in raw_lines if line.strip()]
    #print(saved_lines)
    clean_chunks = [Document(page_content=line) for line in saved_lines]

    def advanced_alphanumeric_tokenizer(text: str):
        return re.findall(r'\b\w+\b', text.lower())

    bm25_search_engine = BM25Retriever.from_documents(
        documents=clean_chunks, 
        k=n,
        preprocess_func=advanced_alphanumeric_tokenizer
    )

    return bm25_search_engine

#DEBUGGING FUNCTIONS
def display_img(base64_image: str):
    img_data = base64.b64decode(base64_image)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imshow("Test Crosshair Placement", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

#FUNCTIONS FOR MODEL
def l_click(coordinates:list,reason:str,wait:int=3):
    try:
        x,y=coordinates
    except ValueError as e:
        return [{'role':"tool","name":"left_click","content":f"Invalid argument passed: {e}"}]
    x_pixel=int((x/1000)*w)
    y_pixel=int((y/1000)*h)
    try:
        pyautogui.click(x_pixel, y_pixel)
    except pyautogui.FailSafeException:
        return {
        "role":"tool",
        "name":"left_click",
        "content":[
            {"type":"text","text":f"fail-safe triggered from mouse moving to a corner of the screen/ invalid coordiantes."}
        ]
    }
    time.sleep(wait)
    #pyautogui.moveTo(0,0)
    image_url=annonated_cursor(coords=[x_pixel,y_pixel])
    utils.log(f"l_click: {x},{y} -> {x_pixel},{y_pixel}")
    return {
        "role":"tool",
        "name":"left_click",
        "content":[
            {"type":"text","text":f"Clicked at [{x},{y}]. Updated screen after clicking on screen:"},
            {"type":"image_url","image_url":{"url":image_url}},
        ]
    }

def r_click(coordinates:list,reason:str,wait:int=3):
    try:
        x,y=coordinates
    except ValueError as e:
        return [{'role':"tool",
                 "name":"right_click",
                 "content":[{"type":"text","text":f"Invalid argument passed: {e}"}]
            }]
    x_pixel=int((x/1000)*w)
    y_pixel=int((y/1000)*h)
    try:
        pyautogui.rightClick(x_pixel, y_pixel)
    except pyautogui.FailSafeException:
        return {
        "role":"tool",
        "name":"right_click",
        "content":[
            {"type":"text","text":f"fail-safe triggered from mouse moving to a corner of the screen/ invalid coordiantes."}
        ]
    }
    time.sleep(wait)
    #pyautogui.moveTo(0,0)
    image_url=annonated_cursor(coords=[x_pixel,y_pixel])
    utils.log(f"r_click: {x},{y} -> {x_pixel},{y_pixel}")
    return {
        "role":"tool",
        "name":"right_click",
        "content":[
            {"type":"text","text":f"Right Clicked at [{x},{y}]. Updated screen after right clicking on screen"},
            {"type":"image_url","image_url":{"url":image_url}},
        ]
    }

def view_screen():
    #pyautogui.moveTo(0,0)
    image_url=get_screenshot()
    return {
        "role":"tool",
        "name":"view_screen",
        "content":[
            {"type":"image_url","image_url":{"url":image_url}}
        ]
    }

def type_text(text:str,textbox_coordinates:list,reason:str,press_enter:bool=False,wait:int=2):
    x,y=textbox_coordinates
    x=(x/1000)*w
    y=(y/1000)*h
    pyautogui.click(x,y)
    time.sleep(0.5)
    #pyautogui.moveTo(0,0)
    pyautogui.write(text)
    time.sleep(1)
    if press_enter:
        pyautogui.hotkey(['enter'])
    time.sleep(wait)
    image_url=get_screenshot()
    return {
        "role":"tool",
        "name":"type_text",
        "content":[
            {"type":"text","text":f"Typed: {text if len(text)<=1001 else text[:1000:]+'...'}. Updated screen after typing text"},
            {"type":"image_url","image_url":{"url":image_url}}
        ]
    }

def press_keyboard_buttons(shortcut:list,app_name:str,reason:str,wait:int=2):
    if app_name.lower()=='none':
        app_name=None
    if app_name:
        status=focus_window(app_name)
        if status==False:
            return {'role':'tool','name':'press_keyboard_buttons',"content":[{"type":"text","text":f"App not found: {app_name}.List of Open Apps:\n{_get_open_apps_raw()}"}]}
    key_str=" + ".join(shortcut)
    try:
        pyautogui.hotkey(shortcut)
        utils.log(f"press_keyboard_buttons: {shortcut}")
        if wait:
            time.sleep(wait)
        image_url=get_screenshot()
        return {
            "role":"tool",
            "name":"press_keyboard_buttons",
            "content":[
                {"type":"text","text":f"Successfully executed: {key_str.strip()}. Updated screen after pressing keyboard keys"},
                {"type":"image_url","image_url":{"url":image_url}}
            ]
        }
    except ValueError as e:
        return {'role':'tool','name':'press_keyboard_buttons','content':[{"type":"text","text":f"Invalid shortcut: {key_str}; {e}"}]}
    except pyautogui.FailSafeException as e:
        return {'role':'tool','name':'press_keyboard_buttons','content':[{"type":"text","text":f"Fail Safe Exception: {e}"}]}
    
def scroll(coordinates:list,reason:str=None,amount:int=6,direction_down:bool=True,wait:int=2):
    x,y=coordinates
    pixel_x=int((x/1000)*w)
    pixel_y=int((y/1000)*h)
    amount*=50
    pyautogui.moveTo(pixel_x,pixel_y)
    if direction_down:
        pyautogui.scroll(-amount)
    else:
        pyautogui.scroll(amount)
    time.sleep(wait)
    #pyautogui.moveTo(0,0)
    image_url=annonated_cursor()
    return {
            "role":"tool",
            "name":"scroll",
            "content":[
                {"type":"text","text":f"Successfully scrolled {amount} units {'down' if direction_down else 'up'} at ({x},{y}). Updated screen after scrolling"},
                {"type":"image_url","image_url":{"url":image_url}}
            ]
        }

def search_shortcut(query:str,return_matches:int=4):
    bm25_search_engine = load_BM25Retriever(n=return_matches)
    matched_documents = bm25_search_engine.invoke(query)

    response = "Matched Shortcuts:\n"
    for idx, doc in enumerate(matched_documents):
        response += f"[Match {idx + 1}]:\n"
        response += str(doc.page_content) + '\n'

    return {"role":"tool","name":"search_shortcut","content":[{"type":"text","text":response}]}
    #return matched_documents

def wait(interval:int,reason:str):
    time.sleep(interval)
    image_url=get_screenshot()
    return {
            "role":"tool",
            "name":"wait",
            "content":[
                {"type":"text","text":f"Wait period of {interval}s is finished. Updated screen after waiting"},
                {"type":"image_url","image_url":{"url":image_url}}
            ]
        }

def report_to_main_agent(response:str = "I have completed the task."):
    agent.name="main_agent",
    agent.tools=utils.load_schema('global_tools.json')
    agent.tool_map=None
    return {
        "role":"tool",
        "name":"report_to_main_agent",
        "content":f"`desktop_copilot` Subagent Response: {response}"
    }

desktop_copilot_tool_map = {
    "view_screen": view_screen,
    "type_text": type_text,
    "press_keyboard_buttons": press_keyboard_buttons,
    "left_click": l_click,
    "right_click": r_click,
    "scroll": scroll,
    "search_shortcut":search_shortcut,
    "report_to_main_agent": report_to_main_agent,
    "wait": wait
}

if __name__=="__main__":
    import json
    time.sleep(3)
    #display_img(base64_image=img)
    a=search_shortcut(query="Open file explorer")
    #print(a)
    print(json.dumps(a,indent=4))
    print(a["content"][0]["text"])
    exit()