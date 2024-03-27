# GUI для [Soul-of-Waifu от jofizcd](https://github.com/jofizcd/Soul-of-Waifu)
### Сейчас это единственная рабочая версия, ни [оригинал](https://github.com/jofizcd/Soul-of-Waifu) ни [lite-версия](https://github.com/Kajitsy/Soul-of-Waifu-Fork/tree/lite) не работают

На данный момент текстовая версия недоступна, возможно появится в будущем, но крайне не обещаю 

Простенький интерфейс, пишите свои идеи либо в [дискорд создателя](https://discord.gg/6UvYzBKCZK) т.к. я там есть, либо в Issues 

Хотите использовать голос от ElevenLabs? Вам [сюда](https://github.com/jofizcd/Soul-of-Waifu), хых
# Что нужно для использования?
- Python
- Библиотеки:
  - `pip install torch --index-url https://download.pytorch.org/whl/cu118`
  - `pip install git+https://codeberg.org/kaiyga/CharacterAITestfork.git@main#egg=characterai`
  - `pip install speechrecognition sounddevice gpytranslate num2words websockets`
- Аккаунт на [old.character.ai](https://old.character.ai/) 
- API ключ сервиса: Открывайте DevTools -> Хранилище -> Локальное хранилище -> https://old.character.ai -> char_token -> Копируйте значение value и вставляете в ID клиента
- ID персонажа: Открывайте чат с нужным вам персонажем -> Из URL-адреса копируйте значение после https://old.character.ai/chat2?char= (если там будет что-то по типу &source=recent-chats, то это копировать не нужно)
- Голос выбирается [отсюда](https://github.com/snakers4/silero-models?tab=readme-ov-file#v4), из строки с ID `v4_ru`

# Отличия версий
<table>
  <thead>
    <tr>
      <th rowspan="2">Версия</th>
      <th colspan="6">Возможности</th>
      <th colspan="1">Работает?</th>
    </tr>
    <tr>
      <th>Текстовый режим</th>
      <th>Разговорный режим</th>
      <th>Озвучка Silero TTS</th>
      <th>Озвучка ElevenLabs</th>
      <th>Графический интерфейс</th>
      <th>Консольный интерфейс</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="1">Оригинальная</td>
      <td>:white_check_mark:</td>
      <td>:white_check_mark:</td>
      <td>:white_check_mark:</td>
      <td>:white_check_mark:</td>
      <td>:negative_squared_cross_mark:</td>
      <td>:white_check_mark:</td>
      <td>:negative_squared_cross_mark:</td>
    </tr>
    <tr>
      <td rowspan="1">GUI</td>
      <td>:negative_squared_cross_mark:</td>
      <td>:white_check_mark:</td>
      <td>:white_check_mark:</td>
      <td>:negative_squared_cross_mark:</td>
      <td>:white_check_mark:</td>
      <td>:negative_squared_cross_mark:</td>
      <td>:white_check_mark:</td>
    </tr>
      <td rowspan="1">Lite</td>
      <td>:white_check_mark:</td>
      <td>:white_check_mark:</td>
      <td>:white_check_mark:</td>
      <td>:negative_squared_cross_mark:</td>
      <td>:negative_squared_cross_mark:</td>
      <td>:white_check_mark:</td>
      <td>:negative_squared_cross_mark:</td>
  </tbody>
</table>
