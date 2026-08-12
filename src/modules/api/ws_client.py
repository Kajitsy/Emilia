import json
import logging
import uuid

from .base_client import BaseClient


class WSClient(BaseClient):
    def __init__(self):
        super().__init__()
        self.ws = None

    async def connect_ws(self):
        """Создает и возвращает WebSocket подключение."""
        if self.ws and not self.ws.closed:
            return self.ws
        try:
            self.ws = await self.session.ws_connect(
                "wss://neo.character.ai/ws/",
                cookies={"HTTP_AUTHORIZATION": f"Token {self.token}"},
                autoclose=False,
            )
            return self.ws
        except Exception as e:
            logging.getLogger(__name__).error(f"WebSocket connection failed: {e}")
            return None

    async def send_message_stream(
        self,
        char_id: str,
        chat_id: str,
        text: str,
        author: dict | None = None,
        attachments: list | None = None,
    ):
        """Отправляет сообщение и возвращает генератор с ответами."""
        if author is None:
            author = {}
        if attachments is None:
            attachments = []

        message = {
            "command": "create_and_generate_turn",
            "payload": {
                "attachments": attachments,
                "character_id": char_id,
                "turn": {
                    "turn_key": {"chat_id": chat_id},
                    "author": author,
                    "candidates": [{"raw_content": text}],
                },
            },
        }
        await self.ws.send_str(json.dumps(message))

        while True:
            msg = await self.ws.recv_str()
            response = json.loads(msg)
            if "turn" not in response:
                raise RuntimeError(response.get("comment", "Unknown error"))
            yield response

    async def edit_message(self, chat_id: str, turn_id: str, text: str):
        """Отправляет запрос на изменение сообщения."""
        payload = {
            "command": "edit_turn_candidate",
            "payload": {
                "turn_key": {"chat_id": chat_id, "turn_id": turn_id},
                "new_candidate_raw_content": text,
            },
        }
        await self.ws.send_str(json.dumps(payload))

        while True:
            response = json.loads(await self.ws.recv_str())
            if "turn" not in response:
                raise RuntimeError(response.get("comment", "Unknown error"))
            if response.get("command") == "update_turn":
                return response

    async def regenerate_turn_stream(
        self, char_id: str, chat_id: str, turn_id: str, user_name: str = ""
    ):
        """Отправляет запрос на перегенерацию сообщения и возвращает поток."""
        message = {
            "command": "generate_turn_candidate",
            "payload": {
                "character_id": char_id,
                "turn_key": {"chat_id": chat_id, "turn_id": turn_id},
                "user_name": user_name,
            },
        }
        await self.ws.send_str(json.dumps(message))

        while True:
            msg = await self.ws.recv_str()
            response = json.loads(msg)
            if "turn" not in response:
                raise RuntimeError(response.get("comment", "Unknown error"))
            yield response

    async def create_new_chat(
        self,
        char_id: str,
        creator_id: str,
        preferred_model_type: str = "MODEL_TYPE_BALANCED",
        scene_id: str = "",
    ):
        """Создает новый чат через WebSocket."""
        chat_id = str(uuid.uuid4())
        payload = {
            "command": "create_chat",
            "payload": {
                "chat": {
                    "character_id": char_id,
                    "chat_id": chat_id,
                    "creator_id": str(creator_id),
                    "preferred_model_type": preferred_model_type,
                    "type": "TYPE_ONE_ON_ONE",
                    "visibility": "VISIBILITY_PRIVATE",
                },
                "with_greeting": True,
            },
        }

        if scene_id:
            payload["payload"]["chat"]["scene_id"] = scene_id

        await self.ws.send_str(json.dumps(payload))

        while True:
            response = json.loads(await self.ws.recv_str())
            if response.get("command") == "create_chat_response":
                return response, chat_id
            elif response.get("command") == "add_turn":
                break
            else:
                raise RuntimeError(response.get("comment", "Unknown error"))

        return None, chat_id
