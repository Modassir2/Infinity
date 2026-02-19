import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import math
import threading
import re
import io
import sys

try:
    import matplotlib
    matplotlib.use("Agg")                       
    import matplotlib.pyplot as plt
    from PIL import Image, ImageTk               
    LATEX_OK = True
except ImportError:
    LATEX_OK = False                             


BG          = "#000000"   
PANEL       = "#050d1a"  
ACCENT      = "#00aaff"   
ACCENT2     = "#00ffcc"  
RED         = "#ff2244"  
ORANGE      = "#ff6600"  
TEXT        = "#cce8ff"  
TEXT_DIM    = "#2a5070"  
USER_BUB    = "#1a1a1a"  
AI_BUB      = "#111111"   
BORDER      = "#0d2a3c"   

FONT_MAIN   = ("Courier New", 14)
FONT_SMALL  = ("Courier New", 12)
FONT_BOLD   = ("Courier New", 14, "bold")  
FONT_CLOCK  = ("Courier New", 36, "bold")   
FONT_DATE   = ("Courier New", 11)           


class JarvisDisc(tk.Canvas):
    """
    Rotating sci-fi disc. States: idle | processing | speaking
    Kept exactly as original — color, speed, label all preserved.
    """

    COLORS = {
        "idle":       (ACCENT,  "#0077cc", ACCENT),
        "processing": (RED,     ORANGE,    "#ff4400"),
        "speaking":   (ACCENT2, "#00ffaa", ACCENT2),
    }
    SPEEDS = {"idle": 0.6, "processing": 3.5, "speaking": 1.8}
    LABELS = {"idle": "IDLE", "processing": "PROC", "speaking": "ACTIVE"}

    def __init__(self, parent, size=260, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=BG, highlightthickness=0, **kwargs)
        self.size  = size
        self.cx    = size // 2
        self.cy    = size // 2
        self.state = "idle"
        self.angle = 0.0
        self.tick  = 0
        self._animate()

    def set_idle(self):       self.state = "idle"
    def set_processing(self): self.state = "processing"
    def set_speaking(self):   self.state = "speaking"

    def _blend(self, hex_fg, alpha, hex_bg=BG):
        def h(c): return tuple(int(c[i:i+2], 16) for i in (1, 3, 5))
        f, b = h(hex_fg), h(hex_bg)
        a = alpha / 255
        r = tuple(int(f[i]*a + b[i]*(1-a)) for i in range(3))
        return "#{:02x}{:02x}{:02x}".format(*r)

    def _draw(self):
        self.delete("all")
        cx, cy = self.cx, self.cy
        core, ring, glow = self.COLORS[self.state]
        t = self.tick / 60.0

        for i in range(5, 0, -1):
            r = 115 + i * 3
            self.create_oval(cx-r, cy-r, cx+r, cy+r,
                             outline=self._blend(glow, 40 - i*6), width=1)

        for i in range(24):
            a1 = math.radians(self.angle + i * 15)
            a2 = math.radians(self.angle + i * 15 + 9)
            r  = 112
            self.create_arc(cx-r, cy-r, cx+r, cy+r,
                            start=math.degrees(a1),
                            extent=math.degrees(a2 - a1),
                            style="arc", outline=ring, width=2)

        for i in range(16):
            a1 = math.radians(-self.angle * 1.3 + i * 22.5)
            a2 = math.radians(-self.angle * 1.3 + i * 22.5 + 12)
            r  = 90
            self.create_arc(cx-r, cy-r, cx+r, cy+r,
                            start=math.degrees(a1),
                            extent=math.degrees(a2 - a1),
                            style="arc", outline=core, width=1)

        ri = 70
        self.create_oval(cx-ri, cy-ri, cx+ri, cy+ri,
                         fill=PANEL, outline=core, width=2)

        for i in range(6):
            a  = math.radians(self.angle * 0.5 + i * 60)
            x2 = cx + (ri - 4) * math.cos(a)
            y2 = cy + (ri - 4) * math.sin(a)
            self.create_line(cx, cy, x2, y2,
                             fill=self._blend(core, 60), width=1)

    
        p = 16 + 4 * math.sin(t * 3.5)
        self.create_oval(cx-p, cy-p, cx+p, cy+p, fill=glow, outline="")

 
        self.create_text(cx, cy + 34,
                         text=self.LABELS[self.state],
                         fill=core, font=("Courier New", 8, "bold"))

 
        for i in range(3):
            a  = math.radians(self.angle * 2 + i * 120)
            ox = cx + 100 * math.cos(a)
            oy = cy + 100 * math.sin(a)
            s  = 4 if self.state == "processing" else 3
            self.create_oval(ox-s, oy-s, ox+s, oy+s, fill=core, outline="")


        L = 14
        corners = [(4,4),(self.size-4,4),(4,self.size-4),(self.size-4,self.size-4)]
        dirs    = [(1,1),(-1,1),(1,-1),(-1,-1)]
        for (x, y), (dx, dy) in zip(corners, dirs):
            self.create_line(x, y, x+dx*L, y,      fill=core, width=2)
            self.create_line(x, y, x,      y+dy*L, fill=core, width=2)

    def _animate(self):
        self.angle = (self.angle + self.SPEEDS[self.state]) % 360
        self.tick += 1
        self._draw()
        self.after(33, self._animate) 


_latex_cache = {}  

def render_latex(expr: str, fontsize=13, color=TEXT) -> "ImageTk.PhotoImage | None":
    if not LATEX_OK:
        return None
    key = (expr, fontsize, color)
    if key in _latex_cache:
        return _latex_cache[key]    
    try:
        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        fig.patch.set_alpha(0)    
        ax.set_axis_off()
        t = ax.text(0.5, 0.5, f"${expr}$",
                    fontsize=fontsize, ha="center", va="center",
                    color=color, transform=ax.transAxes)
        fig.canvas.draw()
        bbox = t.get_window_extent(renderer=fig.canvas.get_renderer())
        w = max(bbox.width + 20, 10)
        h = max(bbox.height + 10, 10)
        fig.set_size_inches(w / fig.dpi, h / fig.dpi)
        fig.canvas.draw()
   
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight",
                    transparent=True, dpi=fig.dpi)
        plt.close(fig)
        buf.seek(0)
        pil_img = Image.open(buf)
        img = ImageTk.PhotoImage(pil_img)
        _latex_cache[key] = img 
        return img
    except Exception:
        return None


def insert_rich_text(widget, text: str, base_tag: str, image_refs: list):

    parts = re.split(r'(\$\$[^$]+\$\$)', text)

    for part in parts:
        if part.startswith("$$") and part.endswith("$$") and len(part) > 4:

            expr = part[2:-2].strip()
            img = render_latex(expr, fontsize=14)
            if img:
                image_refs.append(img)
                widget.insert("end", "\n  ", base_tag)          
                widget.image_create("end", image=img, padx=4, pady=6)
                widget.insert("end", "\n", base_tag)            
            else:
                widget.insert("end", f"\n  {expr}\n", base_tag) 
        else:

            sub_parts = re.split(r'(\$[^$]+\$)', part)
            for sub in sub_parts:
                if sub.startswith("$") and sub.endswith("$") and len(sub) > 2:

                    expr = sub[1:-1].strip()
                    img = render_latex(expr, fontsize=12)
                    if img:
                        image_refs.append(img)
                        widget.image_create("end", image=img, padx=2, pady=2)
                    else:
                        widget.insert("end", sub, base_tag)    
                else:
                    bold_parts = re.split(r'(\*\*[^*]+\*\*)', sub)
                    for bp in bold_parts:
                        if bp.startswith("**") and bp.endswith("**") and len(bp) > 4:
                            widget.insert("end", bp[2:-2], base_tag + "_bold")
                        else:
                            widget.insert("end", bp, base_tag)


class JarvisGUI:

    def __init__(
        self,
        on_send,
        models=None,
        default_model="qwen3:4b",
        on_save=None,
        on_load=None,
        on_clear=None,
    ):
        self.on_send        = on_send
        self.on_save        = on_save
        self.on_load        = on_load
        self.on_clear       = on_clear
        self._models        = models or ["qwen3:4b", "llama3.2", "mistral", "gemma3:4b"]
        self._default_model = default_model
        self.is_processing  = False
        self._image_refs    = []   
        self._ai_buf        = ""   

        self.root = tk.Tk()
        self.root.title("JARVIS")
        self.root.configure(bg=BG)
        self.root.attributes("-fullscreen", True)   
        self.root.bind("<Escape>", lambda e: self._on_exit()) 

        self._build_ui()


    def get_model(self) -> str:
        return self.model_var.get()

    def log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.root.after(0, lambda: self._syslog_insert(f"[{ts}] {msg}\n"))

    def append_user_bubble(self, text: str):
        self.root.after(0, lambda: self._insert_user(text))

    def start_ai_bubble(self, tool_info: str = None):
        if tool_info:
            self.log(f"🔧 {tool_info}")
        self._ai_buf = ""  
        self.root.after(0, self._open_ai_bubble)

    def append_stream_char(self, char: str):
        self._ai_buf += char

    def end_ai_bubble(self):
        self.root.after(0, self._close_ai_bubble)

    def set_state(self, state: str):
        self.root.after(0, lambda: self._apply_state(state))

    def clear_chat_display(self):
        self.root.after(0, self._wipe_chat)

    def reload_chat_display(self, history: list):
        self.root.after(0, lambda: self._redraw_history(history))

    def run(self):
        self.root.mainloop()


    def _build_ui(self):
        self._build_topbar()
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)
        self._build_left_panel(body)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")  # Divider
        self._build_right_panel(body)

    def _build_topbar(self):
        top = tk.Frame(self.root, bg=PANEL, height=46)
        top.pack(fill="x")
        top.pack_propagate(False)

        self._hud_status = tk.Label(
            top, text="● SYSTEM ONLINE",
            font=("Courier New", 13, "bold"),
            bg=PANEL, fg=ACCENT2
        )
        self._hud_status.pack(side="left", padx=16, pady=8)

        ctrl = tk.Frame(top, bg=PANEL)
        ctrl.pack(side="right", padx=10)


        self._mkbtn(ctrl, "EXIT", self._on_exit, RED).pack(side="right", padx=4)


        self._mkbtn(ctrl, "SAVE", self._on_save, TEXT_DIM).pack(side="right", padx=4)


        self._mkbtn(ctrl, "LOAD", self._on_load, TEXT_DIM).pack(side="right", padx=4)


        self._mkbtn(ctrl, "CLEAR", self._on_clear, RED).pack(side="right", padx=4)


        sel = tk.Frame(top, bg=PANEL)
        sel.pack(side="right", padx=10)
        tk.Label(sel, text="MODEL:", font=FONT_SMALL,
                 bg=PANEL, fg=TEXT_DIM).pack(side="left")
        self.model_var = tk.StringVar(value=self._default_model)
        om = tk.OptionMenu(sel, self.model_var, *self._models)
        om.config(bg=PANEL, fg=ACCENT, activebackground=BORDER,
                  activeforeground=ACCENT, font=FONT_SMALL,
                  highlightthickness=0, bd=0)
        om["menu"].config(bg=PANEL, fg=ACCENT, font=FONT_SMALL)
        om.pack(side="left")

    def _build_left_panel(self, parent):
        left = tk.Frame(parent, bg=BG, width=320)
        left.pack(side="left", fill="y", padx=(10, 0), pady=10)
        left.pack_propagate(False)

   
        self.disc = JarvisDisc(left, size=260)
        self.disc.pack(pady=(10, 4))

        self._clock_var = tk.StringVar()
        tk.Label(
            left, textvariable=self._clock_var,
            font=FONT_CLOCK, bg=BG, fg="white"  
        ).pack(pady=(4, 0))

  
        self._date_var = tk.StringVar()
        tk.Label(
            left, textvariable=self._date_var,
            font=FONT_DATE, bg=BG, fg=ACCENT     
        ).pack(pady=(0, 8))

        self._update_clock() 

        tk.Label(left, text="SYSTEM LOG", font=FONT_SMALL,
                 bg=BG, fg=TEXT_DIM).pack(anchor="w", padx=6)
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", padx=6)

        self._syslog_widget = tk.Text(
            left, bg=BG, fg=TEXT_DIM, font=FONT_SMALL,
            insertbackground=ACCENT, bd=0, wrap="word",
            state="disabled"
        )
        self._syslog_widget.pack(fill="both", expand=True, padx=6, pady=4)

    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        
        chat_frame = tk.Frame(right, bg=BG)
        chat_frame.pack(fill="both", expand=True)

        self.chat_box = tk.Text(
            chat_frame,
            bg=BG, fg=TEXT, font=FONT_MAIN,
            insertbackground=ACCENT, bd=0, wrap="word",
            state="disabled",
            spacing1=4, spacing3=4,
            padx=10, pady=10, cursor="arrow"
        )
        self.chat_box.pack(side="left", fill="both", expand=True)


        self.chat_box.bind("<MouseWheel>", lambda e: self.chat_box.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        self.chat_box.tag_configure("user_name",
            foreground=ACCENT, font=("Courier New", 11, "bold")) 
        self.chat_box.tag_configure("user_text",
            foreground=TEXT, lmargin1=16, lmargin2=16,
            background=USER_BUB,  
            spacing1=3, spacing3=6)
        self.chat_box.tag_configure("user_text_bold",
            foreground=TEXT, lmargin1=16, lmargin2=16,
            background=USER_BUB, font=FONT_BOLD,
            spacing1=3, spacing3=6)
        self.chat_box.tag_configure("ai_name",
            foreground=ACCENT2, font=("Courier New", 11, "bold"))  
        self.chat_box.tag_configure("ai_text",
            foreground=TEXT, lmargin1=16, lmargin2=16,
            background=AI_BUB,     
            spacing1=3, spacing3=6)
        self.chat_box.tag_configure("ai_text_bold",
            foreground=TEXT, lmargin1=16, lmargin2=16,
            background=AI_BUB, font=FONT_BOLD,
            spacing1=3, spacing3=6)
        self.chat_box.tag_configure("separator",
            foreground=BORDER)


        inp = tk.Frame(right, bg=PANEL)
        inp.pack(fill="x", pady=(6, 0))
        tk.Frame(inp, bg=BORDER, height=1).pack(fill="x")

        inner = tk.Frame(inp, bg=PANEL)
        inner.pack(fill="x", padx=6, pady=6)

        self.input_var = tk.StringVar()
        self.entry = tk.Entry(
            inner, textvariable=self.input_var,
            bg=BG, fg=TEXT, insertbackground=ACCENT,
            font=FONT_MAIN, bd=0,
            highlightthickness=1,
            highlightcolor=ACCENT,
            highlightbackground=BORDER
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=18, padx=(4, 8))
        self.entry.bind("<Return>", lambda e: self._on_user_send())
        self.entry.focus_set()

        self._mkbtn(inner, "CLEAR", self._on_clear, RED).pack(side="right", padx=4)
        self.send_btn = self._mkbtn(inner, "SEND  ▶", self._on_user_send, ACCENT)
        self.send_btn.pack(side="right")


        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(right, textvariable=self.status_var,
                 font=FONT_SMALL, bg=BG, fg=TEXT_DIM, anchor="w"
                 ).pack(fill="x", pady=(3, 0))


    def _update_clock(self):
        now = datetime.datetime.now()
        self._clock_var.set(now.strftime("%H:%M"))                        
        self._date_var.set(now.strftime("%A, %B %d %Y").upper())            
        self.root.after(1000, self._update_clock)                          



    def _syslog_insert(self, text):
        self._syslog_widget.config(state="normal")
        self._syslog_widget.insert("end", text)
        self._syslog_widget.see("end")
        self._syslog_widget.config(state="disabled")

    def _insert_user(self, text):
        self.chat_box.config(state="normal")
        self.chat_box.insert("end", "\n  YOU\n", "user_name")
        self.chat_box.insert("end", "  ", "user_text")
        insert_rich_text(self.chat_box, text, "user_text", self._image_refs)
        self.chat_box.insert("end", "\n", "user_text")
        self.chat_box.insert("end", f"  {'─'*60}\n", "separator")
        self.chat_box.see("end")
        self.chat_box.config(state="disabled")

    def _open_ai_bubble(self):
        self.chat_box.config(state="normal")
        self.chat_box.insert("end", "\n  ASSISTANT\n", "ai_name")
        self.chat_box.insert("end", "  ...\n", "ai_text") 
        self._ai_start_mark = self.chat_box.index("end-1c linestart")
        self.chat_box.see("end")
        self.chat_box.config(state="disabled")

    def _stream_char(self, char):
        self._ai_buf += char

    def _close_ai_bubble(self):
        self.chat_box.config(state="normal")
        self.chat_box.delete(self._ai_start_mark, "end")
        self.chat_box.insert("end", "  ", "ai_text")
        insert_rich_text(self.chat_box, self._ai_buf, "ai_text", self._image_refs)
        self.chat_box.insert("end", f"\n  {'─'*60}\n", "separator")
        self.chat_box.see("end")
        self.chat_box.config(state="disabled")


    def _wipe_chat(self):
        self.chat_box.config(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.config(state="disabled")

    def _redraw_history(self, history: list):
        self._wipe_chat()
        for msg in history:
            if msg["role"] == "user":
                self._insert_user(msg["content"])
            elif msg["role"] == "assistant":
                self._open_ai_bubble()
                self.chat_box.config(state="normal")
                insert_rich_text(self.chat_box, msg["content"], "ai_text", self._image_refs)
                self.chat_box.config(state="disabled")
                self._close_ai_bubble()


    def _apply_state(self, state: str):
        if state == "idle":
            self.disc.set_idle()
            self.status_var.set("Ready.")
            self._hud_status.config(text="● SYSTEM ONLINE", fg=ACCENT2)
            self.send_btn.config(fg=ACCENT)
            self.is_processing = False
        elif state == "processing":
            self.disc.set_processing()
            self.status_var.set("Processing…")
            self._hud_status.config(text="● PROCESSING", fg=RED)
            self.send_btn.config(fg=TEXT_DIM)
            self.is_processing = True
        elif state == "speaking":
            self.disc.set_speaking()
            self.status_var.set("Generating response…")
            self._hud_status.config(text="● STREAMING", fg=ACCENT2)


    def _on_user_send(self):
        if self.is_processing:
            return
        msg = self.input_var.get().strip()
        if not msg:
            return
        self.input_var.set("")
        self.append_user_bubble(msg)
        self.set_state("processing")
        threading.Thread(target=self.on_send, args=(msg, self), daemon=True).start()


    def _on_save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Conversation"
        )
        if path and self.on_save:
            self.on_save(path)

    def _on_load(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Conversation"
        )
        if path and self.on_load:
            self.on_load(path)

    def _on_clear(self):
        if messagebox.askyesno("Clear Chat", "Clear conversation history?"):
            if self.on_clear:
                self.on_clear()

    def _on_exit(self):
        self.root.destroy()
        sys.exit(0)

    def _mkbtn(self, parent, text, cmd, color):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=PANEL, fg=color,
            activebackground=BORDER, activeforeground=color,
            font=FONT_SMALL, bd=1, relief="flat", cursor="hand2",
            padx=10, pady=4,
            highlightthickness=1, highlightbackground=color
        )