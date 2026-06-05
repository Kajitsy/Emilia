# Класс для получения данных о лимитах пользователя
class CAILimitAPI:
    def __init__(self, client):
        self.client = client  # BaseClient or WSClient

    async def voice_call(self):
        response = await self.client.request(f"feature_limits/voice_call", domain="neo")
        return response

    async def chat_image_attachment(self):
        response = await self.client.request(f"feature_limits/chat_image_attachment", domain="neo")
        return response