import utils

import threading
import time

from openai import  OpenAI
from rich.console import Console
from rich.live import Live
from rich.text import Text


console = Console()

class Config:
    def __init__(self):
        self.update_config()
    def update_config(self):
        config = utils.load_config()
        base_url = config.get("base_url","https://api.openai.com/v1")
        self.url = base_url
        self.searx_url = config.get("searxng_url",None)
        self.n_retry = config.get("n_retry",3)
        self.max_chrs = config.get("max_characters",20000)
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("'api_key' not provided in config.json")
        self.client = OpenAI(base_url=self.url,api_key=self.api_key)
        self.model = config.get("model_id")
        if not self.model:
            raise ValueError("'model_id' not provided in config.json")
        self.ctx_token = config.get("context_length",8192)
        self.buffer_token = int(config.get("buffer_token",2048))
        def_res = {'x':1920,'y':1080}
        self.res_x = int(config.get("screen_resolution",def_res)['x'])
        self.res_y = int(config.get("screen_resolution",def_res)['y'])
        self.mon = int(config.get("primary_monitor",1))
        self.image_n = int(config.get("keep_images",999))



class ToolSet:
    def __init__(self):
        self.tool_set = None
        self.tools = utils.global_tools
        self.tool_map = None



class History:
    def __init__(self):
        #Main items
        self.history = utils.load_history()
        self.user_turn = True
        self.instructions=None
        self.thinking = False
    def update_sysmem_dt(self):
        self.history[0]["content"] = utils.system_prompt.format(tool_set=tools.tool_set,instructions=self.instructions,memory=utils.load_memory(),dt=f"Current Date and Time: {utils.get_datetime()}")
    def update(self):
        self.tokens = utils.count_tokens(messages=self.history,model=config.model,url=config.url,tools=tools.tools,api_key=config.api_key)
    def print_tokens(self,console:Console):
        self.update()
        ctx_token=config.ctx_token
        return console.print(f"Token count: {self.tokens}/{ctx_token}; {(self.tokens/ctx_token)*100:.2f}%", style="yellow")
    def clear_history(self,console:Console):
        console.print("Clearing History...",style="yellow",end="\r")
        if len(self.history)<=1:
            console.print("History is already cleared!",style='yellow')
            return
        old_mem = utils.load_memory() if utils.load_memory() else "None"
        chat_log = ""
        for i in self.history:
            if i["role"] == "user":
                chat_log += "\n[user:]\n"
                if type(i["content"]) == list:
                    content = ""
                    for j in i["content"]:
                        if j.get("text"):
                            content += j.get("text")+'\n'
                    content = content.strip()
                else:
                    content = i["content"]
                chat_log += content
            elif i["role"] == "assistant" and i["content"] != None:
                chat_log += "\n[agent:]\n"
                chat_log += i["content"]
            elif i["role"] == "tool":
                chat_log += "\n[tool:]\n"
                if type(i["content"]) == list:
                    content = ""
                    for j in i["content"]:
                        if j.get("text"):
                            content += j.get("text")+'\n'
                    content = content.strip()
                else:
                    content = i["content"]
                chat_log += content
            else:
                continue
        message = [
            {"role":"system","content":utils.compression_prompt},
            {"role":"user","content":f"Old Profile:\n {old_mem}\n\n Chat Log:\n{chat_log}"}
        ]
        response = config.client.chat.completions.create(
            messages=message,
            model=config.model,
            temperature=0,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        )
        #utils.log(response.choices[0].message.content)
        with open(r".\data\memory.md",'w',encoding='utf-8') as file:
            file.write(response.choices[0].message.content)
        self.history = [{"role":"system","content":utils.system_prompt}]
        self.update_sysmem_dt()
        utils.save_history(self.history)
        self.update()
        console.print(f"{'History Cleared!':<21}",style="yellow")
        self.print_tokens(console=console)
    def truncate_history(self,console:Console):
        count=0
        while len(self.history)>1:
            self.update()
            if self.tokens >= (config.ctx_token-config.buffer_token):
                console.print("Token Limit exceeded, deleting oldest message...",style='yellow',end="\r");count+=1
                #self.clear_history(console=console)
                self.history.pop(1)
                '''
                if self.history[1]["content"]:
                    self.history[1]["content"] = "Message has been removed to manage token limit."
                else:
                    self.history.pop(1)
                '''
                continue
            if count:
                console.print(f"Token Limit was exceeded; Deleted {count} oldest messages!",style='yellow')
            break
    def optimize_history(self):
        h = self.history
        n = config.image_n

        #counting imgs in tools only
        img_index_list=[]
        for i in range(len(h)):
            if h[i]["role"] == "tool" and type(h[i]["content"])==list:
                msg=h[i]['content']
                for j in msg:
                    if j.get('image_url'):
                        img_index_list.append(i)
        if len(img_index_list)>n:
            x=len(img_index_list)-n
            for i in range(x):
                msg=h[img_index_list[i]]['content']
                for j in range(len(msg)):
                    if msg[j].get('image_url'):
                        msg[j]={"type":"text","text":"Attached Image/Screenshot has been removed to save token space and processing time."}
                        break
  
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

config = Config()
tools = ToolSet()
history = History()

if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    console.print("abcedefghijklmnopqrstuvwxyz"*2,end="\r")
    #console.print(f"",end=f"{' ':<54}")
    console.file.write("\r\x1b[K")
    console.print("Hello")