import utils
from classes import agent,config,history


import json
from rich.console import Console
console = Console()
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text
import mss
import base64
import wikipediaapi
import os
import requests

#SUBAGENT FUNCTIONS
from functions.desktop_copilot import desktop_copilot_tool_map, desktop_copilot_system_prompt


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

def get_weather(city:str):
    city=city.lower()
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    geo_response = requests.get(geo_url).json()
    if not geo_response.get("results"):
        return {
            "role":"tool",
            "name":"get_weather",
            "content":f"{city} not found!"
        }
    
    latitude=geo_response['results'][0]['latitude']
    longitude=geo_response['results'][0]['longitude']

    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    weather_data = requests.get(weather_url).json()
    current = weather_data["current_weather"]
    temp = current["temperature"]
    wind = current["windspeed"]
    wind_dir= current["winddirection"]
    is_day = current["is_day"]
    code = current["weathercode"]
    #return current
    return {
        "role":"tool",
        "name":"get_weather",
        "content":f"Time: {utils.get_datetime()}\nTemperature:{temp}°C\nWindspeed: {wind}\nWind Direction: {wind_dir}\nIs Day: {is_day}\nWeather Code: {code}"
    }
def wiki_search(query:str, offset:int=4000) -> dict:
    user_agent = "AIAgentPrototype_Infinity (contact: mimodassir12@gmail.com)"#Wikipedia requires a descriptive User-Agent string to monitor traffic
    wiki = wikipediaapi.Wikipedia(
        user_agent=user_agent,
        language='en',
        extract_format=wikipediaapi.ExtractFormat.WIKI
    )
    
    try:
        page = wiki.page(query)
    except Exception as e:
        return {
            "role":"tool",
            "name":"wiki_search",
            "content":f"An error occured while searching: {e}"
        }

    if not page.exists():
        return {
            "role":"tool",
            "name":"wiki_search",
            "content":f"No Wikipedia page found for query: '{query}'. Try another keyword."
        }
    return {
        "role":"tool",
        "name":"wiki_search",
        "content":[{"type":"text","text":f"# {page.title}\n## Summary: {page.summary[:2000]+'...' if len(page.summary)>2000 else page.summary}\n## Full_content: {page.text[:offset]+'...' if len(page.text)>offset else page.text}\n\nURL: {page.fullurl}"}]
    }

def call_subagent(subagent_name:str,task_description:str):
    subagent_name=subagent_name.lower()
    if subagent_name=="desktop_copilot":
        agent.name="desktop_copilot"
        agent.tool_map=desktop_copilot_tool_map
        agent.tools=utils.load_schema(name=r"desktop_copilot.json")
        history.system_prompt=desktop_copilot_system_prompt
        return {
            "role": "tool",
            "name": "call_subagent",
            "content": f"Task for `desktop_copilot`: {task_description}"
        }
    else:
        return {
            "role":"tool",
            "name":"call_subagent",
            "content":f"Invalid Subagent name called: {subagent_name}"
        }
#----------TEST AND DEBUGGIN AREA----------
#print(get_weather("kolkata"))
#exit()
#------------------------------------------


# GLOBAL VARIABLES, LOT OF PAIN AND BRAIN
global_tool_map = {
    "view_screen":view_screen,
    "get_weather":get_weather,
    "wiki_search":wiki_search,
    "call_subagent":call_subagent
}
agent.name = "main_agent"
agent.tools = utils.load_schema("global_tools.json")
agent.tool_map = global_tool_map


# MAIN FUNCTIONS
def generate():
    output = ""
    tool_dict = {}
    history.update_sysmem_dt()
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
            tools=agent.tools,
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
            history.history.append({"role":"assistant","name":agent.name,"content":output})
    else:
        history.history.append(
            {
                "role":"assistant",
                "name":agent.name,
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
* **`/main_agent`** — Reset back to the main agent.
* **`/agent`** — Print name of the current agent.
* **`/del`** — Delete the current context, without saving to memory.
* **`/exit`** or **`/bye`** — Exit the application.
""")
# The Main loop, lwk even i can't comprehend what i hav built! lol
if __name__=="__main__":
    msg=""
    while True:
        try:
            #console.print()
            if history.user_turn:
                console.print("[USER:]",style=user_color)
                prompt = input()
                if not prompt.strip():
                    console.print("Empty Message detected!",style=warn_color)
                    continue
                command = prompt.strip()
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
                    msg = ""
                    continue
                elif command == '/clear_imgs':
                    h=history.history
                    for i in range(len(h)):
                        if h[i]["role"] == "user" and type(h[i]["content"])==list:
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
                    console.print(Markdown(f"**Model Memory:**\n{utils.load_memory()}"),style=response_color)
                    continue
                elif command == '/main_agent':
                    if agent.name == "main_agent":
                        console.print("main agent already active!",style=warn_color)
                        continue
                    agent.name="main_agent"
                    agent.tool_map=global_tool_map
                    agent.tools=utils.load_schema(r'global_tools.json')
                    history.system_prompt=utils.system_prompt
                    console.print("Switched back to main agent",style=warn_color)
                    continue
                elif command == '/agent':
                    console.print(f"Current agent: {agent.name}",style=warn_color)
                    continue
                elif command == '/help':
                    console.print(help_text)
                    continue
                elif command == '/del':
                    history.history = [{"role":"system","content":utils.system_prompt}]
                    utils.save_history(history.history)
                    console.print("History Context Erased",style=warn_color)
                    continue
                elif command[0] == '/':
                    console.print(f"Unknown Command: {command}",style=warn_color)
                    continue

                if not msg:
                    msg=prompt
                else:
                    msg.append({"type":"text","text":prompt})
                history.history.append({"role":"user","content":msg})
                msg=""
                console.print()
                console.print(f"[{agent.name.upper()}:]",style=assistant_color)

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

                        tool_response = agent.tool_map[name](**args) #Tool Execution is here............

                    except Exception as e:
                        tool_response = {
                            "role":"tool",
                            "name":name,
                            "content":f"An error occured while executing tool call: {e}"
                        }
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
                    output = output[:500]+'...' if len(output)>500 else output
                    output = output.strip()
                    console.print(f"[TOOL_OUTPUT:] {output if output else None}",style=tool_color)

            else:
                history.user_turn = True

            agent.tool_map = global_tool_map if not agent.tool_map else agent.tool_map
            history.truncate_history(console=console)
            history.optimize_history()
            utils.save_history(history.history)
        except KeyboardInterrupt:
            history.user_turn = True
            continue
        except Exception as e:
            history.user_turn = True
            console.print(f"An Error occured: \n{e}",style=error_color)
            utils.log(e,level="ERROR")
            continue