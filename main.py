from ollama import Client
import utils
import ai_tools.functions as functions
import os
import json
import time
from gui.infinity_gui import InfinityGUI
from ai_tools.infinity_tools import TOOLS , TOOL_MAP
import asyncio    
import threading    

client=Client(host='http://localhost:11434')
#To get token count, remove the coments from below and run main.py
#print(f"Tools count: {len(TOOL_MAP)}")
#chrs=len(str(TOOLS))
#print(f"Tokens count: {chrs/4}")
#exit()

import re as _re
import tempfile                                                          
import subprocess                                                           
import sys                                                                  

def _clean_for_tts(text: str) -> str:       
    text = _re.sub(r'\*\*(.+?)\*\*', r'\1', text)  
    text = _re.sub(r'\*(.+?)\*',     r'\1', text)  
    text = _re.sub(r'#+\s*',         '',    text) 
    text = _re.sub(r'`+',            '',    text)  
    text = text.encode('utf-16', 'surrogatepass').decode('utf-16')
    text = ''.join(ch for ch in text if ord(ch) <= 0xFFFF and not (0x2600 <= ord(ch) <= 0x27BF))
    text = _re.sub(                                                        
        u'[\U00010000-\U0010FFFF]', '', text                            
    )                                                                      
    text = _re.sub(r'\s+', ' ', text).strip()                          
    return text                                                            

def speak(text: str):
    def _run():                                                             
        try:                                                                
            import edge_tts                                                 
            clean = _clean_for_tts(text)                                   
            if not clean:                                                   
                return                                                      

            loop = asyncio.new_event_loop()                                
            asyncio.set_event_loop(loop)                                   

            async def _generate(path):                                     
                communicate = edge_tts.Communicate(                        
                    clean,                                                  
                    voice="en-IN-NeerjaNeural" 
                )                                                           
                await communicate.save(path)                               

            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) 
            tmp_path = tmp.name                                             
            tmp.close()                                                     

            loop.run_until_complete(_generate(tmp_path))                   
            loop.close()                                                    

            size = os.path.getsize(tmp_path)                               
            if size == 0:                                                   
                return                                                      

            if sys.platform == "win32":                                    

                duration_sec = int(size / 3000) + 2                     
                ps_cmd = (                                                  
                    "Add-Type -AssemblyName presentationCore;"             
                    "$p = New-Object System.Windows.Media.MediaPlayer;"    
                    f"$p.Open([uri]'{tmp_path}');"                        
                    "$p.Play();"                                           
                    f"Start-Sleep -Seconds {duration_sec};"                
                    "$p.Close()"                                           
                )                                                           
                subprocess.run(                                             
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                    creationflags=0x08000000                                
                )                                                           
            else:                                                           
                subprocess.run(["xdg-open", tmp_path])                     

            os.remove(tmp_path)                                            

        except Exception as e:                                              
            print(f"[TTS Error] {e}")                                      

    threading.Thread(target=_run, daemon=False).start()                    

def select_user():
    db = functions._load_memory_db()
    print("\n" + "="*40)
    print("       INFINITY — USER LOGIN")
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

if not utils.get_contacts():
    print("\n" + "="*50)
    print("Contacts not loaded")
    print("Would you like to load contacts")
    print("  (y = yes, n = skip for this session)")
    print("="*50)
    cont_choice = input("  >> ").strip().lower()
    if cont_choice=='y':
        print(utils.extract_vcf_contacts())
        input("Press Enter to continue...")
    else:
        print("  Skipping Loading Contacts. You can set it up later by restarting Infinity.\n")

if not utils.get_wh_session():
    print("\n" + "="*50)
    print("  WHATSAPP NOT SET UP")
    print("  Would you like to set up WhatsApp now?")
    print("  (y = yes, n = skip for this session)")
    print("="*50)
    wh_choice = input("  >> ").strip().lower()
    if wh_choice == 'y':
        utils.setup_wh_session()
    else:
        print("  Skipping WhatsApp setup. You can set it up later by restarting Infinity.\n")

user_memory = functions.view_memory()


SYSTEM_PROMPT = f"""You are Infinity, a smart assistant with access to tools.
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
            model="qwen3:4b",
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
    print(f"Infinity: {reply}\n")    

    history = utils.turnacate_history(history)
    utils.save_history(history)
    return reply, tool_summary

def handle_message(user_msg: str, gui: InfinityGUI):
    try:
        gui.set_state("processing")
        reply, tool_summary = chat(user_msg, gui)

        gui.set_state("speaking")
        gui.start_ai_bubble(tool_info=tool_summary)
        for ch in reply:
            gui.append_stream_char(ch)
            time.sleep(0.008)
        gui.end_ai_bubble()

        if gui.voice_enabled:
            speak(reply)

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

print("Infinity Online.\n")

gui = InfinityGUI(
    on_send  = handle_message,
    on_save  = on_save,
    on_load  = on_load,
    on_clear = on_clear,
)

gui.log(f"INFINITY online. Logged in as: {logged_in_user}") 

if len(history) > 1:
    gui.reload_chat_display(history)

gui.run()