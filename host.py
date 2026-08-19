from flask import Flask, request, render_template,redirect,url_for
from classes import config,agent,history
from main import global_tool_map

web=Flask(__name__)
agent.tool_map=global_tool_map
auth=False
password = "Moda"
response = None

def generate(prompt):
    history.history.append({"role":"user","content":prompt})
    response = config.client.chat.completions.create(
        model=config.model,
        messages=history.history,
        tools=agent.tools
    )
    return response.choices[0].message.content


@web.route('/login',methods=["GET","POST"])
def login():
    global auth
    if request.method=="GET":
        return render_template("login.html",msg=None)
    if request.method=="POST":
        a=request.form.get('password')
        if a==password:
            auth=True
            return redirect(url_for('home'))
        else:
            auth=False
            return render_template("login.html",msg="Incorrect Password!")

@web.route('/home',methods=["GET","POST"])
def home():
    global response
    if not auth:
        return redirect(url_for('login'))

    if request.method == "GET":
        output=""
        for msg in history.history:
            if msg["role"] in ("user","assistant"):
                if msg.get("content"):
                    output += f"[{msg['role'].upper()}:]\n{msg['content']}\n\n"
        return render_template('home.html',response=output)
    elif request.method == "POST":
        prompt = request.form.get('prompt')
        response = generate(prompt)
        history.history.append({"role":"assistant","content":response})
        return redirect(url_for('home'))

web.run(host='0.0.0.0',port=8003,debug=True)