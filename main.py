from ollama import Client
import utils
import ai_tools.functions as functions
import os
import json
import time
from gui.jarvis_gui import JarvisGUI
from ai_tools.jarvis_tools import TOOLS , TOOL_MAP

client=Client(host='http://localhost:11434')

def select_user():
    db = functions._load_memory_db()
    print("\n" + "="*40)
    print("       JARVIS — USER LOGIN")
    print("="*40)

    if db:
        print("Registered users: " + ", ".join(db.keys()))
    else:
        print("No users registered yet.")

    print("\nType your name to login, or type 'new' to register.")
    print("="*40)

    while True:
        choice = input(">> ").strip()

        if choice.lower() == "new":
            new_name = input("Enter your new username: ").strip()
            if not new_name:
                print("Username cannot be empty. Try again.")
                continue
            result = functions.register_user(new_name)
            print(result)
            return new_name
        
        elif choice in db:
            print(f"Welcome back, {choice}!")
            return choice
        
        else:
            print(f"User '{choice}' not found. Type 'new' to register or try again.")

logged_in_user = select_user()

functions.current_user = logged_in_user

user_memory = functions.view_memory()

#history = utils.load_history()


SYSTEM_PROMPT = f"""You are Jarvis, a smart assistant with access to tools.
The current user is: {logged_in_user}
What you remember about {logged_in_user}:
{user_memory}

When you call a tool and receive a result, always trust the result and report it back to the user directly.
Never say you cannot do something if a tool has already done it — just confirm what happened.
If the user asks for multiple things at once, call all the required tools together in a single response.
You have access to wiki_search — use it to look up information when needed. If a topic is ambiguous, search 
again with a more specific term.

"""


history = [
    {'role': 'system', 'content': SYSTEM_PROMPT}
]

def chat(message, gui=None):

    global history
    history.append({'role': 'user', 'content': message})
    tool_summary = None
    tool_summaries = []

    while True:
        response = client.chat(
            model=gui.get_model() if gui else "qwen3:4b",
            messages=history,
            keep_alive=-1,
            tools=TOOLS,
            options={
                'num_ctx': 8192
            }
        )

        msg = response['message']

        if msg.get('tool_calls'):

            tool_calls_serializable = [
                {
                    "function": {
                        "name": tc.function.name,          
                        "arguments": tc.function.arguments 
                    }
                }
                for tc in msg['tool_calls']
            ]

            history.append({
                'role': 'assistant', 
                'content': msg.get('content') or '',
                'tool_calls': tool_calls_serializable

            })

            for tool_call in msg['tool_calls']:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']

                print(f"🔧 Calling tool: {tool_name}({tool_args})")
                if gui: gui.log(f"Tool: {tool_name}({tool_args})")
                

                func = TOOL_MAP.get(tool_name)
                if func:
                    result = func(**tool_args) if tool_args else func()
                else:
                    result = "Tool Not Found"

                tool_summaries.append(f"{tool_name}: {result}")

                history.append({
                    'role': 'tool',
                    'name': tool_name,
                    'content': result
                })

            tool_summary = " | ".join(tool_summaries)

        else:
            reply = msg['content']
            break

    history.append({'role': 'assistant', 'content': reply})
    print(f"Jarvis: {reply}\n")    

    history = utils.turnacate_history(history)
    utils.save_history(history)
    return reply, tool_summary

def handle_message(user_msg: str, gui: JarvisGUI):
    try:
        gui.set_state("processing")
        reply, tool_summary = chat(user_msg, gui)

        gui.set_state("speaking")
        gui.start_ai_bubble(tool_info=tool_summary)
        for ch in reply:
            gui.append_stream_char(ch)
            time.sleep(0.008)
        gui.end_ai_bubble()

        utils.save_history(history)
        gui.log("Done.")

    except Exception as exc:
        gui.end_ai_bubble()
        gui.start_ai_bubble()
        for ch in f"[ERROR] {exc}":
            gui.append_stream_char(ch)
        gui.end_ai_bubble()
        gui.log(f"ERROR: {exc}")
    finally:
        gui.set_state("idle")

def on_save(path: str):
    with open(path, "w") as f:
        json.dump(history, f, indent=2)
    gui.log(f"Saved: {os.path.basename(path)}")

def on_load(path: str):
    global history
    with open(path) as f:
        history = json.load(f)
    gui.reload_chat_display(history)
    gui.log(f"Loaded: {os.path.basename(path)}")

def on_clear():
    global history
    history = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    gui.clear_chat_display()
    utils.save_history(history)
    gui.log("History cleared.")

print("Jarvis Online.\n")

gui = JarvisGUI(
    on_send  = handle_message,
    on_save  = on_save,
    on_load  = on_load,
    on_clear = on_clear,
)

gui.log(f"JARVIS online. Logged in as: {logged_in_user}") 

if len(history) > 1:
    gui.reload_chat_display(history)

gui.run()