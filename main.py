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
    if subagent_name=="desktop_copilot":
        agent.name="desktop_copilot"
        agent.tool_map=desktop_copilot_tool_map
        agent.tools=utils.load_schema(name=r"desktop_copilot.json")
        history.system_prompt=desktop_copilot_system_prompt
        return {
            "role": "tool",
            "name": "call_subagent",
            "content": f"Switched to desktop_copilot for: {task_description}"
        }
    else:
        return {
            "role":"tool",
            "name":"call_subagent",
            "content":f"Invalid Subagent name called: {subagent_name}"
        }
#----------TEST AND DEBUGGIN AREA----------
#print(json.dumps(wiki_search("Infinity")),indent=4)
#exit()
#------------------------------------------


# GLOBAL VARIABLES, LOT OF PAIN AND BRAIN
global_tool_map = {
    "view_screen":view_screen,
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
    with Live(console=console,auto_refresh=False,vertical_overflow='visible') as live:
        text=Text("Processing...",style="yellow")
        live.update(text,refresh=True)
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
* **`/clear`** — Truncate current conversation history.
* **`/update`** — Reload configuration and refresh memory settings.
* **`/tokens`** — Print token usage statistics.
* **`/memory`** — View active model memory.
* **`/main_agent`** — Reset back to the main agent.
* **`/agent`** — Print name of the current agent.
* **`/exit`** or **`/bye`** — Exit the application.
""")
# The Main loop, even i can't comprehend what i hav built!
if __name__=="__main__":
    while True:
        try:
            #console.print()
            if history.user_turn:
                console.print("[USER:]",style=user_color)
                prompt = input()
                if not prompt.strip():
                    console.print("Empty Message detected!",style=warn_color)
                    continue
                elif prompt == '/exit' or prompt == '/bye':
                    exit()
                elif prompt == '/clear':
                    history.clear_history(console)
                    continue
                elif prompt == '/update':
                    config.update_config()
                    #history.update_sysmem()
                    history.update()
                    console.print("Updated Config!",style=warn_color)
                    continue
                elif prompt == '/tokens':
                    history.print_tokens(console=console)
                    continue
                elif prompt == '/memory':
                    console.print(Markdown(f"**Model Memory:**\n{utils.load_memory()}"),style=response_color)
                    continue
                elif prompt == '/main_agent':
                    agent.name="main_agent"
                    agent.tool_map=global_tool_map
                    agent.tools=utils.load_schema(r'global_tools.json')
                    history.system_prompt=utils.system_prompt
                    console.print("Switched back to main agent",style=warn_color)
                    continue
                elif prompt == '/agent':
                    console.print(f"Current agent: {agent.name}",style=warn_color)
                    continue
                elif prompt == '/help':
                    console.print(help_text)
                    continue
                elif prompt.strip()[0] == '/':
                    console.print(f"Unknown Command {prompt.strip()}",style=warn_color)
                    continue
                history.history.append({"role":"user","content":prompt + '\n\nTime Stamp: ' + utils.get_datetime()})
                console.print()
                console.print(f"[{agent.name.upper()}:]",style=assistant_color)

            tool_dict = generate() #Main func call is here..........

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
                        tool_response = agent.tool_map[name](**args)
                    except Exception as e:
                        tool_response = {
                            "role":"tool",
                            "name":name,
                            "content":f"An error occured while executing tool call:{e}"
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
            history.truncate_history(console=console)
            history.optimize_history()
            utils.save_history(history.history)
        except KeyboardInterrupt:
            history.user_turn = True
            continue
        #except Exception as e:
            #history.user_turn = True
            #console.print(f"An Error occured: \n{e}",style=error_color)
            #continue