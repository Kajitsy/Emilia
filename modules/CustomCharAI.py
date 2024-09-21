import aiohttp
from modules.config import getconfig

async def request(endpoint, data = None, method = "get", neo = False):
    headers = {
        "Content-Type": 'application/json',
        "Authorization": f'Token {getconfig("client", configfile="charaiconfig.json")}'
    }

    if neo:
        url = f"https://neo.character.ai/{endpoint}"
    else:
        url = f"https://plus.character.ai/{endpoint}"

    async with aiohttp.ClientSession() as session:
        if method == "get":
            async with session.get(url, headers=headers, params=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get data, status code: {response.status}")
        elif method == "post":
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get data, status code: {response.status}")
        else:
            raise ValueError("Invalid method")

async def get_character(character_id):
    data = {
        "external_id": character_id
    }
    response = await request("chat/character/info/", data, "post")
    return response['character']

async def tts(candidateId, roomId, turnId, voiceId=None, voiceQuery=None):
    """voiceId or voiceQuery required"""
    if voiceId == "":
        data = {
            'candidateId': candidateId,
            'roomId': roomId,
            'turnId': turnId,
            'voiceId': voiceId,
            'voiceQuery':voiceQuery
        }
    else:
        data = {
            'candidateId': candidateId,
            'roomId': roomId,
            'turnId': turnId,
            'voiceId': voiceId
        }
    response = await request("multimodal/api/v1/memo/replay", data, "post", neo=True)
    return response

async def get_recommend_chats():
    response = await request("recommendation/v1/user", neo=True)
    return response['characters']

async def get_recent_chats():
    response = await request("chats/recent", neo=True)
    return response['chats']

async def get_me():
    response = await request("chat/user/")
    return response['user']['user']