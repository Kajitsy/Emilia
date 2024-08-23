import random, json, pyvts
from modules.config import writeconfig

plugin_info = {
    "plugin_name": "Emilia VTube",
    "developer": "kajitsy",
    "authentication_token_path": "./token.txt"
}

myvts = pyvts.vts(plugin_info)

async def VTubeConnect():
    """
    Подключение к Vtube Studio
    """
    try:
        await myvts.connect()
        try:
            await myvts.read_token()
            await myvts.request_authenticate()
        except:
            await myvts.request_authenticate_token()
            await myvts.write_token()
            await myvts.request_authenticate()
    except:
        writeconfig('vtubeenable', False)

async def SetCustomParameter(name, value=50, min=-100, max=100):
    """
    Лучше всего использовать для создания параметров плагина

    CustomParameter("EmiEyeX", -100, 100, 0)
    """

    try:
        await myvts.request(
            myvts.vts_request.requestCustomParameter(name, min, max, value)
        )
    except:
        await VTubeConnect()
        await myvts.request(
            myvts.vts_request.requestCustomParameter(name, min, max, value)
        )
    await myvts.close()

async def DelCustomParameter(name):
    """
    Удаление кастомных параметров

    DelCustomParameter("EmiEyeX")
    """

    try:
        await myvts.request(
            myvts.vts_request.requestDeleteCustomParameter(name)
        )
    except:
        await VTubeConnect()
        await myvts.request(
            myvts.vts_request.requestDeleteCustomParameter(name)
        )
    await myvts.close()

def RandomBetween(a, b):
    """
    Просто случайное число, не более.

    RandomBetween(-90, -75)
    """
    return random.randint(a, b)

async def AddVariables():
    """
    Создаёт все нужные переменные
    """

    parameters = ["EmiFaceAngleX", "EmiFaceAngleY", "EmiFaceAngleZ",
                  "EmiEyeOpenLeft", "EmiEyeOpenRight",
                  "EmiEyeX", "EmiEyeY", "EmiMountSmile", "EmiMountX"]
    for param in parameters:
        await SetCustomParameter(param)

async def DelVariables():
    """
    Удаляет все нужные переменные
    """

    parameters = ["EmiFaceAngleX", "EmiFaceAngleY", "EmiFaceAngleZ",
                  "EmiEyeOpenLeft", "EmiEyeOpenRight",
                  "EmiEyeX", "EmiEyeY", "EmiMountSmile", "EmiMountX"]
    for param in parameters:
        await DelCustomParameter(param)

async def UseEmote(emote):
    """
    Управляет значениями переменных, беря их и их значение из Emotes.json
    """

    def getemotes(emote):
        with open("Emotes.json", "r") as f:
            emotes_data = json.load(f)
        emote_data = emotes_data[emote]
        return emote_data

    emote_data = getemotes(emote)
    rndm = RandomBetween
    names = []
    values = []
    for parameter_name, parameter_value in emote_data.items():
        if parameter_name == "EyesOpen":
            eyesopen_value = eval(parameter_value)
            values.append(eyesopen_value)
            values.append(eyesopen_value)
            names.append("EmiEyeOpenRight")
            names.append("EmiEyeOpenLeft")
        else:
            names.append(parameter_name)
            value = eval(parameter_value)
            values.append(value)

    await VTubeConnect()
    for i, name in enumerate(names):
        value = values[i]
        await myvts.request(
            myvts.vts_request.requestCustomParameter(
                parameter=name,
                min=0,
                max=100,
                default_value=value
            )
        )
    await myvts.close()

