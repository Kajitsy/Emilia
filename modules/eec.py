import random, json
from pyvts import vts
from modules.config import writeconfig

plugin_info = {
    "plugin_name": "Emilia VTube",
    "developer": "kajitsy",
    "authentication_token_path": "./token.txt"
}

class EEC():
    def __init__(self):
        self.myvts = vts(plugin_info)

    async def VTubeConnect(self):
        """
        Подключение к Vtube Studio
        """
        try:
            await self.myvts.connect()
            try:
                await self.myvts.read_token()
                await self.myvts.request_authenticate()
            except:
                await self.myvts.request_authenticate_token()
                await self.myvts.write_token()
                await self.myvts.request_authenticate()
        except:
            writeconfig("vtubeenable", False)

    async def SetCustomParameter(self, name, value=50, min=-100, max=100):
        """
        Лучше всего использовать для создания параметров плагина

        CustomParameter("EmiEyeX", -100, 100, 0)
        """

        try:
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(name, min, max, value)
            )
        except:
            await self.VTubeConnect()
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(name, min, max, value)
            )
        await self.myvts.close()

    async def DelCustomParameter(self, name):
        """
        Удаление кастомных параметров

        DelCustomParameter("EmiEyeX")
        """

        try:
            await self.myvts.request(
                self.myvts.vts_request.requestDeleteCustomParameter(name)
            )
        except:
            await self.VTubeConnect()
            await self.myvts.request(
                self.myvts.vts_request.requestDeleteCustomParameter(name)
            )
        await self.myvts.close()

    def RandomBetween(self, a, b):
        """
        Просто случайное число, не более.

        RandomBetween(-90, -75)
        """
        return random.randint(a, b)

    async def AddVariables(self):
        """
        Создаёт все нужные переменные
        """

        parameters = ["EmiFaceAngleX", "EmiFaceAngleY", "EmiFaceAngleZ",
                      "EmiEyeOpenLeft", "EmiEyeOpenRight",
                      "EmiEyeX", "EmiEyeY", "EmiMountSmile", "EmiMountX"]
        for param in parameters:
            await self.SetCustomParameter(param)

    async def DelVariables(self):
        """
        Удаляет все нужные переменные
        """

        parameters = ["EmiFaceAngleX", "EmiFaceAngleY", "EmiFaceAngleZ",
                      "EmiEyeOpenLeft", "EmiEyeOpenRight",
                      "EmiEyeX", "EmiEyeY", "EmiMountSmile", "EmiMountX"]
        for param in parameters:
            await self.DelCustomParameter(param)

    async def UseEmote(self, emote):
        """
        Управляет значениями переменных, беря их и их значение из Emotes.json
        """

        def getemotes(emote):
            with open("Emotes.json", "r") as f:
                emotes_data = json.load(f)
            emote_data = emotes_data[emote]
            return emote_data

        emote_data = getemotes(emote)
        rndm = self.RandomBetween
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

        # await self.VTubeConnect()
        for i, name in enumerate(names):
            value = values[i]
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(
                    parameter=name,
                    min=0,
                    max=100,
                    default_value=value
                )
            )
        # await self.myvts.close()

