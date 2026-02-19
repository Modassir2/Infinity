import json
import os

os.chdir(os.path.dirname(__file__))

def save_history(history):
    with open('./saved_data/history.json', 'w') as f:
        json.dump(history, f, indent=4)

def load_history():
    if os.path.exists('./saved_data/history.json'):
        with open('history.json', 'r') as f:
            return json.load(f)
    return [{'role': 'system', 'content': "You are Jarvis."}]

def turnacate_history(history):
    if len(history) > 31:                              
        return [history[0]] + history[-30:]            
    return history