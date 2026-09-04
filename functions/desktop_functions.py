import utils
from classes import config

import base64
import time
import re

import pyautogui
import mss
import win32gui
import win32con
import cv2
import numpy as np
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document


w = config.res_x
h = config.res_y
mon =  config.mon
desktop_tools_instructions = """**YOU MUST ALWAYS START BY GENERATING STEPS BEFORE TAKING ANY ACTION.**
1. Analyze the task completely
2. Generate a detailed step-by-step plan marked as "Step 1:", "Step 2:", etc.
3. Present this plan to the user and WAIT for acknowledgment/confirmation before proceeding
4. DO NOT execute any tool calls (left_click, type_text, etc.) until the user confirms the plan

## EXECUTION ORDER:
Step Generation → User Confirmation → Execute Step 1 → Verify & Report → Execute Step 2 → ... Continue until complete

## EXECUTION PHASE (ONLY AFTER STEP CONFIRMATION):
After the user acknowledges the plan:
1. Execute each step in strict order
2. At each step, search for relevant keyboard shortcuts using search_shortcut tool
3. Use the appropriate tool (left_click, type_text, press_keyboard_buttons, scroll, etc.) to perform the action
4. Verify completion by taking a screenshot and analyzing the result
5. Acknowledge the result and move to the next step

## PRIORITY RULES:
-. NEVER execute actions before generating and confirming steps with the user
-. Acknowledge your actions after each step and confirm status to the user before moving forward
-. Follow the workflow order strictly - no deviations
-. Ask the user for clarification if any task details are vague
-. Improvise or edit steps if circumstances require it (but inform the user)
-. Do not submit forms, emails, payments, bookings - only fill in details and ask user to continue
-. The `type_text` tool automatically brings the textbox to focus, no need to click first"""

#HELPER FUNCTIONS
def get_screenshot(mon:int=mon):
    with mss.mss() as screen:
        screen.shot(output="monitor-2.png", mon=mon)
    with open('monitor-2.png','rb') as img:
        base64img=base64.b64encode(img.read()).decode('utf-8')
    return f"data:image/png;base64,{base64img}"

def annonated_cursor(image_url:str=None,coords:list[int,int]=None):
    if not image_url:
        image_url = get_screenshot()
    if not coords:
        coords = pyautogui.position()
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

def generate_feedback(action: str,img_b64: str):
    sys_prompt = """Given the screenshot and reasoning, generate a valid feedback if the action was completed successfuly or failed. If action is failed, explain the reason of failure.
    The red cross is the coordinates where the user clicked at to complete the action. If the click was at wrong coordinates then tell the user to correct the coordinates. (for eg. You clicked at wroing coordinates / You clicked on file explorer icon mistakenly etc).
    If the action is compeleted successfuly then validate the action (for eg. You successfully opened xyz app.), no explanations required."""
    messages = [
        {"role":"system","content":sys_prompt},
        {"role":"user","content":[{"type":"text","text":f"Action: {action}"},{"type":"image_url","image_url":{"url":img_b64}}]}
    ]
    response = config.client.chat.completions.create(
        model=config.model,
        messages=messages,
    )
    return response.choices[0].message.content

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
    feedback = generate_feedback(img_b64=image_url,action=reason)
    return {
        "role":"tool",
        "name":"left_click",
        "content":[
            {"type":"text","text":f"Clicked at [{x},{y}]. {feedback}"},
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
    feedback = generate_feedback(img_b64=image_url,action=reason)
    return {
        "role":"tool",
        "name":"right_click",
        "content":[
            {"type":"text","text":f"Right Clicked at [{x},{y}]. {feedback}"},
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
    image_url=annonated_cursor(coords=[x,y])
    feedback = generate_feedback(img_b64=image_url,action=reason)
    return {
        "role":"tool",
        "name":"type_text",
        "content":[
            {"type":"text","text":f"Typed: {text if len(text)<=1001 else text[:1000:]+'...'}. {feedback}"},
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

desktop_tool_map = {
    "view_screen": view_screen,
    "type_text": type_text,
    "press_keyboard_buttons": press_keyboard_buttons,
    "left_click": l_click,
    "right_click": r_click,
    "scroll": scroll,
    "search_shortcut":search_shortcut,
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