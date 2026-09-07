import utils
from classes import tools,config,history

import json
import os
import base64

from rich.console import Console
console = Console()
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text
import mss

#TOOLSETS and FUNCTIONS
from functions.web_search_tools import web_search_tool_map,web_search_instructions
from functions.desktop_functions import desktop_tool_map,desktop_tools_instructions
from functions.file_modification_functions import file_modification_tool_map,file_modification_instructions
from functions.read_file_functions import read_file_tool_map,read_file_instructions
from functions.coding_functions import coding_tool_map,coding_instructions

tool_set_map={
    "web_search_tools": {"tool_map":web_search_tool_map,"instructions":web_search_instructions},
    "desktop_tools": {"tool_map":desktop_tool_map,"instructions":desktop_tools_instructions},
    "file_modification_tools": {"tool_map":file_modification_tool_map,"instructions":file_modification_instructions},
    "read_file_tools": {"tool_map":read_file_tool_map,"instructions":read_file_instructions},
    "coding_tools": {"tool_map":coding_tool_map,"instructions":coding_instructions},
}


warn2_color = "orange"#"df7700ff"
warn_color = "yellow"#"ffa600"
user_color = "green"#"#008A00"
assistant_color = "green"#"#00A800"
tool_color = "gray39"#"#303030"
response_color = "grey53"#"#636262"
error_color = "red"#"#ad0000"
thinking_color = "cyan"


# GLOBAL FUNCTIONS
def view_screen(mon:int=config.mon):
    with mss.mss() as screen:
        screen.shot(output="monitor-2.png", mon=mon)
    with open('monitor-2.png','rb') as img:
        base64img=base64.b64encode(img.read()).decode('utf-8')
    image_url = f"data:image/png;base64,{base64img}"
    return {
        "role":"tool",
        "name":"view_screen",
        "content":[
            {"type":"text","text":f"User's screenshot at {utils.get_datetime()}"},
            {"type":"image_url","image_url":{"url":image_url}}
        ]
    }

def add_memory(memory:str):
    current_memory = utils.read_memory() or ""
    if current_memory and not current_memory.endswith("\n"):
        current_memory += "\n"
    utils.write_memory(current_memory + memory)
    return {
        "role":"tool",
        "name":"add_memory",
        "content":"Memory added successfully."
    }

def remove_memory(memory:str):
    current_memory = utils.read_memory() or ""
    if memory not in current_memory:
        return {
            "role":"tool",
            "name":"remove_memory",
            "content":"Memory block was not found; memory was not changed."
        }
    utils.write_memory(current_memory.replace(memory, "", 1))
    return {
        "role":"tool",
        "name":"remove_memory",
        "content":"Memory removed successfully."
    }

def patch_memory(old_value:str, new_value:str):
    current_memory = utils.read_memory() or ""
    if old_value not in current_memory:
        return {
            "role":"tool",
            "name":"patch_memory",
            "content":"Old value was not found; memory was not changed."
        }
    utils.write_memory(current_memory.replace(old_value, new_value, 1))
    return {
        "role":"tool",
        "name":"patch_memory",
        "content":"Memory patched successfully."
    }

def get_tools(tool_set:str):
    tool_set=tool_set.lower()
    try:
        t = utils.load_schema(name=tool_set)
        t_map = tool_set_map[tool_set]["tool_map"] | global_tool_map
    except (FileNotFoundError,KeyError):
        return {
            "role":"tool",
            "name":"get_tools",
            "content":f"Invalid Tool Set Name: {tool_set}"
        }
    tools.tool_set=tool_set
    tools.tool_map=t_map
    tools.tools=t
    history.instructions=tool_set_map[tool_set].get("instructions",None)
    return {
        "role": "tool",
        "name": "get_tools",
        "content": f"Switched tools to {tool_set}"
    }


#----------TEST AND DEBUGGIN AREA----------
#print(json.dumps(fetch_url_content(url="https://www.timeanddate.com/worldclock/india/kolkata"),indent=4))
#exit()
#------------------------------------------


# GLOBAL VARIABLES, LOT OF PAIN AND BRAIN
global_tool_map = {
    "get_tools":get_tools,
    "view_screen":view_screen,
    "add_memory":add_memory,
    "remove_memory":remove_memory,
    "patch_memory":patch_memory
}
tools.tool_map=global_tool_map


# MAIN FUNCTIONS
def generate():
    output = ""
    tool_dict = {}
    history.update_sysmem_dt()
    history.optimize_history()
    history.truncate_history(console=console)
    with Live(console=console,auto_refresh=False,vertical_overflow="ellipsis") as live:
        text=Text("Processing...",style="yellow")
        live.update(text,refresh=True)
        #utils.log(json.dumps(history.history,indent=4),path=r'.\data\debug.log',mode='a',level="DEBUG")
        #utils.log(agent.name,path=r'.\data\debug.log',mode='a',level="DEBUG")
        #utils.log(json.dumps(agent.tools,indent=4),path=r'.\data\debug.log',mode='a',level="DEBUG")
        response = config.client.chat.completions.create(
            messages=history.history,
            model=config.model,
            stream=True,
            tools=tools.tools,
            #extra_body={"chat_template_kwargs": {"enable_thinking": True}}
        )
        try:
            for chunk in response:
                delta = chunk.choices[0].delta
                #Thinking timer!
                if hasattr(delta,'reasoning_content'):
                    if not history.thinking:
                        history.start_timer(live,color=thinking_color)
                elif history.thinking:
                    history.stop_timer(live)
                #Content        
                if delta.content:
                    content =  delta.content
                    output += content
                    live.update(Markdown(output+'\n'),refresh=True)
                #TOOL CALL!!.....
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        index = tool_call.index
                        if index not in tool_dict:
                            tool_dict[index] = {
                                "id":"",
                                "name":"",
                                "arguments_str":""
                            }
                        if tool_call.id:
                            tool_dict[index]["id"] = tool_call.id
                        if tool_call.function and tool_call.function.name:
                            tool_dict[index]["name"] = tool_call.function.name
                        if tool_call.function and tool_call.function.arguments:
                            arg = tool_call.function.arguments
                            tool_dict[index]["arguments_str"] += arg
        except KeyboardInterrupt:
            history.stop_timer(live)
            tool_dict={}
    if not tool_dict:
        if output:
            history.history.append({"role":"assistant","content":output})
    else:
        history.history.append(
            {
                "role":"assistant",
                "content": output if output else None,
                "tool_calls":[
                    {"id":tool_dict[id]["id"],"type":"function","function":{"name":tool_dict[id]["name"],"arguments":tool_dict[id]["arguments_str"]}} for id in tool_dict
                ]
            }
        )
    return load_args(tool_dict)

def load_args(tool_dict:dict):
    if not tool_dict:
        return {}
    for id in tool_dict:
        args = tool_dict[id]['arguments_str']
        try:
            tool_dict[id]['args'] = json.loads(args) if args else {}
        except json.decoder.JSONDecodeError as e:
            return {"error":f"Invalid Tool Call Generated: {e}\n{args}"}
    return tool_dict



help_text = Markdown("""
# 🛠️ Command Help Menu

* **`/help`** — Display this menu.
* **`/image`** — Attach image by full path (eg /image C:/image path.png/).
* **`/remove_imgs`** — Removed all attached images.
* **`/clear_imgs`** — Remove all images from context history.
* **`/clear`** — Truncate current conversation history.
* **`/update`** — Reload configuration and refresh memory settings.
* **`/tokens`** — Print token usage statistics.
* **`/memory`** — View active model memory.
* **`/general_tools`** — Reset back to general tools set.
* **`/tools`** — Print currently active tool set.
* **`/del`** — Delete the current context, without saving to memory.
* **`/exit`** or **`/bye`** — Exit the application.
""")
# The Main loop, lwk even i can't comprehend what i hav built! lol
if __name__=="__main__":
    msg=""
    history.truncate_history(console=console)
    while True:
        try:
            #console.print()
            if history.user_turn:
                console.print("[USER:]",style=user_color)
                prompt = input()
                if not prompt.strip():
                    console.print("Empty Message detected!",style=warn_color)
                    continue
                command = prompt.strip().lower()
                if command == '/exit' or command == '/bye':
                    exit()
                elif command[:6] == "/image":
                    path = command[7:].strip()
                    if path.startswith('"'):
                        path = path[1:-1]
                    if not os.path.isfile(path):
                        console.print(f"Invalid Path: {path}",style=warn_color)
                        continue
                    base64url=utils.get_base64_url(path)
                    if not msg:
                        msg = [{"type":"image_url","image_url":{"url":base64url}}]
                    else:
                        msg.append({"type":"image_url","image_url":{"url":base64url}})
                    console.print(f"Image Attached: {path}",style=warn_color)
                    continue
                elif command == '/remove_imgs':
                    console.print("Removed Attached Images",style=warn_color)
                    msg = ""
                    continue
                elif command == '/clear_imgs':
                    h=history.history
                    for i in range(len(h)):
                        if h[i]["role"] in ("user","tool") and type(h[i]["content"])==list:
                            content = h[i]["content"]
                            for j in range(len(content)):
                                if content[j].get("image_url"):
                                    content[j]={"type": "text", "text": "User removed the attached image from history."}
                    console.print("All Images Cleared from History!",style=warn_color)
                    utils.save_history(history.history)
                    continue
                elif command == '/clear':
                    history.clear_history(console)
                    utils.save_history(history.history)
                    continue
                elif command == '/update':
                    config.update_config()
                    history.update()
                    console.print("Updated Config!",style=warn_color)
                    continue
                elif command == '/tokens':
                    history.print_tokens(console=console)
                    continue
                elif command == '/memory':
                    console.print(Markdown(f"**Model Memory:**\n{utils.read_memory()}"),style=response_color)
                    continue
                elif command == '/general_tools':
                    if tools.tool_set == "general_tools":
                        console.print("General tools are already active!",style=warn_color)
                        continue
                    get_tools("general_tools.json")
                    console.print("Switched back General tools",style=warn_color)
                    continue
                elif command == '/tools':
                    console.print(f"Current Tool Set: {tools.tool_set}",style=warn_color)
                    continue
                elif command == '/help':
                    console.print(help_text)
                    continue
                elif command == '/del':
                    history.history = [{"role":"system","content":utils.system_prompt}]
                    history.update_sysmem_dt()
                    utils.save_history(history.history)
                    console.print("History Context Erased",style=warn_color)
                    continue
                elif command[0] == '/':
                    console.print(f"Unknown Command: {command}",style=warn_color)
                    continue

                prompt = prompt + f"\nTimestamp: {utils.get_datetime()}"
                if not msg:
                    msg = prompt
                else:
                    msg.append({"type":"text","text":prompt})
                history.history.append({"role":"user","content":msg})
                msg=""
                console.print()

                console.print("[Infinity:]",style=assistant_color)
                utils.save_history(history.history)

            tool_dict = generate() #Main func call is here............

            if tool_dict:
                history.user_turn = False
                if tool_dict.get("error"):
                    console.print(f"[TOOL_CALL:] {tool_dict.get('error')}; Retrying TOOL_CALL")
                    continue
                for id in tool_dict:
                    name = tool_dict[id]["name"]
                    args = tool_dict[id]["args"]
                    console.print(f"[TOOL_CALL:] Executeing: {name}({args})",style=tool_color)
                    try:

                        tool_response = tools.tool_map[name](**args) #Tool Execution is here............

                    except Exception as e:
                        tool_response = {
                            "role":"tool",
                            "name":name,
                            "content":f"An error occured while executing tool call: {e}"
                        }
                    if tool_response:
                        tool_response['tool_call_id'] = tool_dict[id]["id"]
                        history.history.append(tool_response)

                        #printing tool response...lwk, nothing important
                        if type(tool_response["content"]) == list:
                            output = ''
                            for i in tool_response["content"]:
                                    if i.get("text"):
                                        output += i.get("text") + '\n'
                            output = output.strip()
                        else:
                            output = tool_response["content"].strip()
                        output = output.strip().splitlines()
                        if len(output)>1:
                            print_output = output[0][:100].strip() +'...'
                        elif len(output[0])>100:
                            print_output = output[0][:100]+'...'
                        else:
                            print_output = output[0] if output else None
                        console.print(f"[TOOL_OUTPUT:] {print_output}",style=tool_color,markup=False)

            else:
                history.user_turn = True

            utils.save_history(history.history)
        except KeyboardInterrupt:
            history.user_turn = True
            continue
        except Exception as e:
            utils.log(e,level="FATAL")
            history.user_turn = True
            console.print(f"An Error occured: \n{e}",style=error_color,markup=False)
            continue