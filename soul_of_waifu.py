import os
import asyncio
import threading
import torch
import time
import re
import json
import requests
import sounddevice as sd
from gpytranslate import Translator
from characterai import PyAsyncCAI
import speech_recognition as sr
from num2words import num2words
import tkinter as tk
from tkinter import messagebox, ttk

local_file = 'russian.pt'
device = torch.device('cuda')
stop_main_flag = False
sample_rate = 48000
put_accent = True
put_yo = True

def numbers_to_words(text):
    def _conv_num(match):
        return num2words(int(match.group()), lang='ru')
    return re.sub(r'\b\d+\b', _conv_num, text)

def download_russian_pt(progressbar, progress_label):
    if not os.path.isfile(local_file):  
        url = 'https://models.silero.ai/models/tts/ru/v4_ru.pt'
        try:
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            with open(local_file, 'wb') as f:
                for data in response.iter_content(chunk_size=1024):
                    f.write(data)
                    progress = min(100, int(100 * f.tell() / total_size))
                    progressbar['value'] = progress
                    progress_label.config(text=f"Скачивание: {progress}%")
                    setup_window.update_idletasks()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка скачивания файла: {e}")
            return

        messagebox.showinfo("Сообщение", "Файл успешно скачан.")
    
    progress_label.config(text="")
    progressbar['value'] = 0
    setup_window.update_idletasks()

def load_config(char_entry, client_entry, speaker_entry):
    if os.path.exists('config.json'):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            char_entry.insert(0, config.get('char', ''))
            client_entry.insert(0, config.get('client', ''))
            speaker_entry.insert(0, config.get('speaker', ''))
            global char, client, speaker
            char = char_entry.get()
            client = client_entry.get()
            speaker = speaker_entry.get()


def setup_config(char_entry, client_entry, speaker_entry):
    global char, client, speaker
    char = char_entry.get()
    client = client_entry.get()
    speaker = speaker_entry.get()

    config = {
        "char": char,
        "client": client,
        "speaker": speaker
    }

    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)

    messagebox.showinfo("Сообщение", "Конфигурация сохранена в config.json")

def show_conversation_window():
    global character_label, user_label
    conversation_window = tk.Toplevel()
    conversation_window.title("Диалог")

    user_label = tk.Label(conversation_window, text="Пользователь:", wraplength=200, justify="left")
    user_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    character_label = tk.Label(conversation_window, text="Ответ: пусто", wraplength=200, justify="left")
    character_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

def start_main():
    global main_thread
    main_thread = threading.Thread(target=lambda: asyncio.run(main()))
    main_thread.start()

async def main():
    while True:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            translation_label.config(text="Говорите...")
            user_label.config(text="Говорите...")
            audio = recognizer.listen(source)
        try:
            msg1 = recognizer.recognize_google(audio, language="ru-RU")
        except sr.UnknownValueError:
            translation_label.config(text="Скажите ещё раз...")
            user_label.config(text="Скажите ещё раз...")
            continue
        chat = await PyAsyncCAI(client).chat2.get_chat(char)
        author = {'author_id': chat['chats'][0]['creator_id']}
        user_label.config(text="Вы: " + msg1)
        translation_label.config(text="Ответ: генерация...")
        character_label.config(text="Ответ: генерация...")
        async with PyAsyncCAI(client).connect() as chat2:
            data = await chat2.send_message(
                char, chat['chats'][0]['chat_id'],
                msg1, author
            )
        textil = data['turn']['candidates'][0]['raw_content']
        translation = await Translator().translate(textil, targetlang="ru")
        nums = numbers_to_words(translation.text)
        model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        model.to(device)
        audio = model.apply_tts(text=nums,
                                speaker=speaker,
                                sample_rate=sample_rate,
                                put_accent=put_accent,
                                put_yo=put_yo)
        print(f"Ответ: {nums}")
        translation_label.config(text="Ответ: " + translation.text)
        character_label.config(text="Ответ: " + translation.text)
        sd.play(audio, sample_rate)
        time.sleep(len(audio - 5) / sample_rate)
        sd.stop()

def run_script():
    global setup_window, translation_label
    setup_window = tk.Tk()
    setup_window.title("Настройка конфигурации")

    char_label = tk.Label(setup_window, text="ID персонажа:")
    char_label.grid(row=0, column=0)
    char_entry = tk.Entry(setup_window)
    char_entry.grid(row=0, column=1)

    client_label = tk.Label(setup_window, text="ID клиента:")
    client_label.grid(row=1, column=0)
    client_entry = tk.Entry(setup_window)
    client_entry.grid(row=1, column=1)

    speaker_label = tk.Label(setup_window, text="Голос:")
    speaker_label.grid(row=2, column=0)
    speaker_entry = tk.Entry(setup_window)
    speaker_entry.grid(row=2, column=1)

    load_config(char_entry, client_entry, speaker_entry)  

    save_button = tk.Button(setup_window, text="Сохранить", command=lambda: setup_config(char_entry, client_entry, speaker_entry))
    save_button.grid(row=3, columnspan=2)

    start_button = tk.Button(setup_window, text="Запустить", command=start_main)
    start_button.grid(row=4, columnspan=2)

    show_dialog_button = tk.Button(setup_window, text="Показать диалог", command=lambda: show_conversation_window())
    show_dialog_button.grid(row=5, columnspan=2)

    progress_label = tk.Label(setup_window, text="")
    progress_label.grid(row=6, columnspan=2)

    progressbar = ttk.Progressbar(setup_window, orient='horizontal', length=200, mode='determinate')
    progressbar.grid(row=7, columnspan=2)

    threading.Thread(target=lambda: download_russian_pt(progressbar, progress_label)).start()

    translation_label = tk.Label(setup_window, text="")
    translation_label.grid(row=8, columnspan=2)

    setup_window.mainloop()

if __name__ == "__main__":
    run_script()