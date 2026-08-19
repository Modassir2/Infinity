import utils
from openai import  OpenAI
from rich.console import Console
from rich.live import Live
from rich.text import Text
import threading
import time
#import functions.global_functions as global_functions #Don't try this ever again, trust me its not worth it! Never will be.
console = Console()

compression_prompt = """
You are an advanced memory consolidation subsystem. Review the given chat history and generate a updated memory profile. 
Your task is only to generate user profile from the chat history, do not output anything else.
Generate a updated profile with any new preferences, context, facts, project details, or decisions.
Do not output anything else, only output the updated markdown profile.
Maintain the Markdown format cleanly. Delete outdated information. Use the following format:

# Memory
## User Core Identity & Preferences
- Name: Not Provided / [NAME]
- Preferences: What the user prefers and likes (eg- color, food, tone etc).
- Dislikes: What the user hates or dislikes.

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
  - user realted facts. eg:
  - user's phone is black
  - user's computer has <computer specs>
  - user lives in <city> etc.
  - remove facts that are no longer required or unnessesary."""

class Config:
    def __init__(self):
        self.update_config()
    def update_config(self):
        config = utils.load_config()
        base_url, port = config.get("base_url","https://api.openai.com/v1"), int(config.get("port"))
        self.url = f"{base_url}:{port}" if port else base_url
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("'api_key' not provided in config.json")
        self.client = OpenAI(base_url=self.url,api_key=self.api_key)
        self.model = config.get("model_id")
        if not self.model:
            raise ValueError("'model_id' not provided in config.json")
        self.ctx_token = config.get("context_length",8192)
        self.buffer_token = int(config.get("buffer_token",2048))
        self.image_tokens = int(config.get("image_tokens",1032))
        def_res = {'x':1920,'y':1080}
        self.res_x = int(config.get("screen_resolution",def_res)['x'])
        self.res_y = int(config.get("screen_resolution",def_res)['y'])
        self.mon = int(config.get("primary_monitor",1))
        self.image_n = int(config.get("keep_images",999))

config = Config()

class Agent:
    def __init__(self):
        self.name = "main_agent"
        self.tools = utils.load_schema("global_tools.json")
        self.tool_map = {}

agent = Agent()

class History:
    def __init__(self):
        #Main items
        self.history = utils.load_history()
        self.system_prompt=utils.system_prompt
        self.user_turn = True
        self.update()
        self.thinking = False
    def update_sysmem_dt(self):
        self.history[0]["content"] = self.system_prompt + '\n\n' + utils.load_memory() + f"\nCurrent Date and Time: {utils.get_datetime()}"
    def update(self):
        self.tokens = utils.count_tokens(messages=self.history,model=config.model,url=config.url,tools=agent.tools,api_key=config.api_key)
    def print_tokens(self,console:Console):
        self.update()
        ctx_token=config.ctx_token
        return console.print(f"Token count: {self.tokens}/{ctx_token}; {(self.tokens/ctx_token)*100:.2f}%", style="yellow")
    def clear_history(self,console:Console):
        old_mem = utils.load_memory() if utils.load_memory() else "None"
        chat = ''
        for i in self.history:
            if i["role"] == "user":
                chat += "\n[user:]\n"
                if type(i["content"]) == list:
                    content = ""
                    for j in i["content"]:
                        if j.get("text"):
                            content += j.get("text")+'\n'
                    content = content.strip()
                else:
                    content = i["content"]
                chat += content
            elif i["role"] == "assistant" and i["content"] != None:
                chat += "\n[agent:]\n"
                chat += i["content"]
            elif i["role"] == "tool":
                chat += "\n[tool:]\n"
                if type(i["content"]) == list:
                    content = ""
                    for j in i["content"]:
                        if j.get("text"):
                            content += j.get("text")+'\n'
                    content = content.strip()
                else:
                    content = i["content"]
                chat += content
            else:
                continue
        message = [
            {"role":"system","content":compression_prompt},
            {"role":"user","content":f"Old Profile:\n {old_mem}\n\n Chat Log:\n{chat}"}
        ]
        console.print("Trucating History...",style="yellow",end="\r")
        response = config.client.chat.completions.create(
            messages=message,
            model=config.model,
            temperature=0,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        )
        #utils.log(response.choices[0].message.content)
        with open(r".\data\memory.txt",'w') as file:
            file.write(response.choices[0].message.content)
        self.history = [{"role":"system","content":utils.system_prompt}]
        self.update_sysmem_dt()
        utils.save_history(self.history)
        self.update()
        console.print(f"{'History Truncated!':<21}",style="yellow")
        self.print_tokens(console=console)
    def truncate_history(self,console:Console):
        if self.tokens >= (config.ctx_token-config.buffer_token):
            self.clear_history(console=console)
    def optimize_history(self):
        history = self.history
        n = config.image_n
        imgs=0;img_index_list=[];x=0
        for i in history:
            msg=i['content']
            if type(msg)==list:
                for j in msg:
                    if j.get('image_url'):
                        imgs+=1
                        img_index_list.append(x)
                        break
            x+=1
        if imgs>n:
            y=len(img_index_list)-n
            for i in range(y):
                x=history[img_index_list[i]]['content']
                for j in range(len(x)):
                    if x[j].get('image_url'):
                        x[j]={"type":"text","text":"Attached Image/Screenshot has been removed to save token space and processing time."}
            return history
        else:
            return history
    def start_timer(self,live:Live,color:str="cyan"):
        def run_timer():
            start_timer = time.time()
            while self.thinking:
                elapsed = time.time() - start_timer
                text=Text(f"Thinking... {elapsed:.1f}s",style=color)
                live.update(text,refresh=True)
                time.sleep(0.1)
        timer_thread = threading.Thread(target=run_timer,daemon=True)
        self.thinking = True
        timer_thread.start()
    def stop_timer(self,live:Live):
        if self.thinking:
            self.thinking = False
            time.sleep(0.02)
            #console.file.write("\r\x1b[K")
            live.update("",refresh=True)

history = History()

if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    console.print("abcedefghijklmnopqrstuvwxyz"*2,end="\r")
    #console.print(f"",end=f"{' ':<54}")
    console.file.write("\r\x1b[K")
    console.print("Hello")