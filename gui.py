print('''
   _____             __         ____   _       __      _ ____     
  / ___/____  __  __/ /  ____  / __/  | |     / ____ _(_/ ____  __
  \__ \/ __ \/ / / / /  / __ \/ /_    | | /| / / __ `/ / /_/ / / /
 ___/ / /_/ / /_/ / /  / /_/ / __/    | |/ |/ / /_/ / / __/ /_/ / 
/____/\____/\__,_/_/   \____/_/       |__/|__/\__,_/_/_/  \__,_/  
                                                                  
                                     [code by jofi|gui by kajitsy]
''')
import tkinter as tk
from tkinter import ttk
import subprocess
import ast
import tkinter.font as tkFont

process = None
root = tk.Tk()
root.title("Soul of Waifu GUI")
root.configure(bg='#ffffff')

def load_config():
    with open('config.py', 'r') as f:
        lines = f.readlines()
    config = {}
    for line in lines:
        key, value = line.strip().split(' = ', 1)
        config[key] = ast.literal_eval(value)
    return config

def save_config():
    with open('config.py', 'w') as f:
        f.write(f"client = '{client_entry.get()}'\n")
        f.write(f"char = '{char_entry.get()}'\n")
        f.write(f"speaker = '{speaker_var.get()}'\n")
    indicator_label.config(text="Настройки сохранены")

def run_script():
    global process
    if process:
        process.terminate()
    indicator_label.config(text="ИИ запущена")
    process = subprocess.Popen(["python", "soul_of_waifu.py"])

def stop_script():
    global process
    if process:
        process.terminate()
        process = None
    indicator_label.config(text="ИИ не запущена")

font = tkFont.Font(family="Roboto", size=12)

colors = {
    "primary": "#9a609a",
    "secondary": "#f0f0f0",
    "accent": "#ff4081",
    "text": "#212121",
    "white": "#ffffff"
}

frame = tk.Frame(root, bg=colors["white"])
frame.pack(padx=20, pady=20)

tk.Label(frame, text="API ключ Сharacter.AI:", bg=colors["primary"], fg=colors["white"], font=font).grid(row=0, column=0, sticky=tk.E, padx=10, pady=10)
tk.Label(frame, text="Персонаж:", bg=colors["primary"], fg=colors["white"], font=font).grid(row=1, column=0, sticky=tk.E, padx=10, pady=10)
tk.Label(frame, text="Голос:", bg=colors["primary"], fg=colors["white"], font=font).grid(row=2, column=0, sticky=tk.E, padx=10, pady=10)

client_entry = tk.Entry(frame, bg=colors["secondary"], fg=colors["text"], font=font)
char_entry = tk.Entry(frame, bg=colors["secondary"], fg=colors["text"], font=font)
voice_entry = tk.Entry(frame, bg=colors["secondary"], fg=colors["text"], font=font)

speaker_var = tk.StringVar()
speaker_dropdown = ttk.Combobox(frame, textvariable=speaker_var, values=["aidar", "baya", "kseniya", "xenia", "eugene", "random"], state="readonly")

client_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
char_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
speaker_dropdown.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)

config = load_config()
client_entry.insert(0, config.get('client', ''))
char_entry.insert(0, config.get('char', ''))
speaker_var.set(config.get('speaker', ''))

save_button = tk.Button(frame, text="Сохранить", bg=colors["accent"], fg=colors["white"], font=font, command=save_config)
run_button = tk.Button(frame, text="Запустить", bg=colors["accent"], fg=colors["white"], font=font, command=run_script)
stop_button = tk.Button(frame, text="Остановить", bg=colors["accent"], fg=colors["white"], font=font, command=stop_script)
indicator_label = tk.Label(frame, bg=colors["secondary"], fg=colors["text"], font=font)

save_button.grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
indicator_label.grid(row=3, column=1, sticky=tk.W, padx=10, pady=10)
indicator_label.config(text="ИИ не запущена")
run_button.grid(row=3, column=2, sticky=tk.W, padx=10, pady=10)
stop_button.grid(row=3, column=3, sticky=tk.W, padx=10, pady=10)

root.mainloop()