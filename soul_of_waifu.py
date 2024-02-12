import os
import asyncio
import torch
import time
import re
import sounddevice as sd
from gpytranslate import Translator
from characterai import PyAsyncCAI
from whisper_mic import WhisperMic
from num2words import num2words
from config import char, client, speaker
local_file = 'russian.pt'
device = torch.device('cuda')

sample_rate = 48000
put_accent=True
put_yo=True

if not os.path.isfile(local_file):
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt',
                                   local_file)  

#nums to worn
def numbers_to_words(text):
    def _conv_num(match):
        return num2words(int(match.group()), lang='ru')
    return re.sub(r'\b\d+\b', _conv_num, text)

async def main():
    while True:
        chat = await PyAsyncCAI(client).chat2.get_chat(char)
        author = {'author_id': chat['chats'][0]['creator_id']}
        mic = WhisperMic(model='small', english=False, energy=300, pause=1, mic_index=1)
        msg1 = mic.listen()
        print("Ты сказал:", msg1)
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
        print(f"Персонаж ответил: {nums}")
        sd.play(audio, sample_rate)
        time.sleep(len(audio - 5) / sample_rate)
        sd.stop()
asyncio.run(main())