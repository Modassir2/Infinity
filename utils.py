import json
from datetime import datetime
import base64
from typing import Literal

import requests


system_prompt = """# Role and Core Objective
You are Infinity, a smart AI assistant with access to multiple tool sets. Respond to user's request directly without tool call when required. If the task cannot be completed with provided tools, call `get_tools` function to get a different set of tools as per the task.

# Tool Sets
Use a tool set to only when it is required or user asks explicitly. Follow the instructions of each tool set strictly when using that tool set.
Current tool set: {tool_set}

# Instructions for {tool_set}
{instructions}

{memory}

# Current Date and Time
{dt}
"""

compression_prompt = """
You are an advanced memory consolidation agent. Review the given chat log and generate a updated memory profile. 
Your task is only to generate user profile from the chat history, do not output anything else.
Generate a updated profile with any new preferences, context, facts, project details, or decisions.
Do not output anything else, only output the updated markdown profile.
Maintain the Markdown format cleanly. Delete outdated information. Use the following format, addition to the format is allowed if required:

# Memory
## User Core Identity & Preferences
- Name: Not Provided / [NAME]
- Preferences: None / What the user prefers and likes (eg- color, food, tone etc).
- Dislikes: None / What the user hates or dislikes.

## Recent Chat memory
1. eg. 26th June 2026 3:05 pm - Mention the timestamp of conversations for each point.
2. <timestamp> - Summarize the current chat both user request and agents reponse, keep it short and crisp.
3. <timestamp> - The list must be in descending order, newest first.
4. <timestamp> - Keep maximum of 20 points here and if more than 20 points then remove the oldest memory first.
5. <timestamp> - Keep maximum old chat memory possible while adding new memory without exceeding the limits.
6. <timestamp> - Keep maximum details in least words.

## Ongoing Task (if any)
- Current Task: Task provided by user and not yet completed by agent. If no incomplete task then only None.
- Task Details (if Task): Mention any nessesary details required for the task.
- Addtional Context (if task): More background context or None.

## Facts and Information
- Only keep very important or needed facts here. Do not store unneccesary facts.
- user realted facts. eg:
- user's phone is black
- user's computer has <computer specs>
- user lives in <city> etc.
- remove facts that are no longer required or unnessesary.
  
## Add More if required (for eg- user asks explicitly)"""

with open(r'.\\global_tools.json') as f:
    global_tools=json.load(f)
def load_schema(name:str):
    if not name.endswith(".json"):
        name+=".json"
    path = r".\\tools_schema\\" + name
    with open (path,'r') as file:
        schema = json.load(file)
    return schema + global_tools

def load_config(path:str=r".\config.json"):
    file = open(path,'r')
    config = json.load(file)
    file.close()
    return config

def get_base64_url(path:str):
    with open(path,'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/png;base64,{b64}"

def log(line:str,path:str=r'.\data\logs.log',level:Literal["DEBUG","INFO","WARN","ERROR","FATAL"]="INFO",mode='r'):
    if level=="DEBUG":
        with open(path,mode,encoding='utf-8') as f:
            f.write(line)
        return
    d = {
        "timestamp": get_datetime(),
        "level": str(level),
        "details":str(line)
    }
    with open(path,'a') as file:
        file.write(json.dumps(d)+'\n')

def save_history(history:list):
    #log("History Saved utils.txt save_history() line 63",path=r".\data\debug.txt",level="DEBUG")
    with open(r'.\data\history.json','w',encoding='utf-8') as f:
        json.dump(history,f,indent=4)
    
def load_history():
    try:
        with open(r".\data\history.json",'r',encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        #return [{"role":"system","content":system_prompt.format(tool_set="global_tools",instructions=None,memory=load_memory(),dt=get_datetime())}]
        return [{"role":"system","content":system_prompt}]
    
def load_memory():
    try:
        with open(r'.\data\memory.md','r',encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None

def get_datetime():
    now = datetime.now()
    dt = now.strftime(r"%A, %d-%B-%Y, %I:%M %p")
    return dt

def count_tokens(messages: list[dict],model,url,api_key, tools = None) -> int:
    history = messages.copy()
    if len(history)<=1:
        history.append({"role":"user","content":"Hello"})
    headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
    }
    payload = {
    "model": model,
    "messages": history
    }
    if tools:
        payload["tools"] = tools

    for _ in range(5):
        response = requests.post(
            f"{url}/v1/chat/completions/input_tokens",
            json=payload,
            headers=headers,
            timeout=300,
        )
        if response.status_code==500:
            continue
        break
    #print("STATUS:", response.status_code)
    #print("RESPONSE:", response.text)
    response.raise_for_status()
    return response.json()["input_tokens"]


if __name__ == "__main__":
    print("Testing")
    with open(r"C:\Users\Modassir\Downloads\history.json",'r') as file:
        message = json.load(file)
    with open(r"C:\Users\Modassir\Projects\Infinity\Infinity\tools_schema\global_tools.json",'r') as file:
        tools = json.load(file)
    print(count_tokens(messages=message,image_tokens=1032,model="qwen3.5_4b",url="http://127.0.0.1:8002",tools=tools))
    input("Press enter to exit...")