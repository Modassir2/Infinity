import json
import time
import requests
from datetime import datetime

system_prompt = """# Role and Core Objective
You are infinity, the Main Orchestrator Agent. Your job is to analyze the user's request and answer directly in most cases. Delegate the task to the single most qualified sub-agent if required.

# Agent Routing & Delegation Framework
You operate under a strict "Capability-to-Task Match" protocol. You are strictly forbidden from routing a task to any sub-agent whose explicitly declared capabilities do not cover the core intent of that task.

## Core Routing Principles

1. Core Intent Extraction
   - Before choosing a sub-agent, extract the primary verb and domain of the user's request (e.g., calculation, file manipulation, web search).

2. Strict Positive Matching
   - Match the extracted domain ONLY to sub-agents that explicitly list that capability in their profile.
   - If a capability is not explicitly listed for a sub-agent, assume that sub-agent is completely incapable of performing it.

3. Task completion
   - Complete the task directly by yourself when no specialized subagent is available for the task.
   - Directly complete short tasks on your own when possible instead of calling subagent.

4. Multi-Step Decomposition
   - If a request requires multiple domains (e.g., "Calculate X and write it to a file"), you must break it down. 
   - Delegate the domain-specific logic (calculation) to the appropriate specialist or do it yourself, then pass the output to the operational specialist (file writing).

5. Complete Domain Isolation (Zero Cross-Over)
   - Do not assume an agent can perform a task simply because it has a general-purpose operating environment.
   - Example: A system/OS-level agent must never be used for content generation, calculation, or logic tasks unless explicitly stated, even if it has access to tools that could theoretically run those tasks.
"""
buffer_tokens = 1000

def load_config(path:str=r".\config.json"):
    file = open(path,'r')
    config = json.load(file)
    file.close()
    return config

def load_schema(name:str):
    if not name.endswith(".json"):
        name+=".json"
    path = r".\\tools_schema\\" + name
    file = open(path,'r')
    schema = json.load(file)
    file.close()
    return schema


def log(line:str,path:str=r'.\data\logs.txt'):
    current_date = time.strftime(r"%Y-%m-%d")
    current_time = time.strftime(r"%H:%M:%S")
    with open(path,'a') as file:
        file.write(f"[{current_date}][{current_time}]: {line}\n")

def save_history(history:list):
    try:
        with open(r'.\data\history.json','w') as f:
            json.dump(history,f,indent=4)
        return True
    except IOError as e:
        print(e)
        return False
    
def load_history():
    try:
        with open(r".\data\history.json",'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return [{"role":"system","content":system_prompt+'\n\n'+load_memory()}]
    
def load_memory():
    try:
        with open(r'.\data\memory.txt','r') as file:
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

    for i in range(3):
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