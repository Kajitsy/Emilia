import pyvts, asyncio, os, json

def getconfig(value, def_value, configfile = 'emotesconfig.json'):
    if os.path.exists(configfile):
        with open(configfile, 'r') as configfile:
            config = json.load(configfile)
            return config.get(value, def_value)
    else:
        return def_value

class EEC():
    """
    EMC - Emilia Emotes Core
    """
    
    plugin_info = {
        "plugin_name": "Emilia VTube",
        "developer": "kajitsy",
        "authentication_token_path": "./token.txt"
    }

    myvts = pyvts.vts(plugin_info)

    async def VTubeConnect(self):
        """
        Подключение к Vtube Studio
        """

        await self.myvts.connect()
        try:
            await self.myvts.read_token()
            await self.myvts.request_authenticate()
        except:
            await self.myvts.request_authenticate_token()
            await self.myvts.write_token()
            await self.myvts.request_authenticate()

    async def AddCustomParameter(self, name, value=0, min=-100, max=100):
        """
        Лучше всего использовать для создания параметров плагина\n

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

    async def SetCustomParameters(self, names, values):
        """
        Управляет значениями сразу нескольких переменных\n

        SetCustomParameters(["EmiEyeX", "EmiEyeY"], [50, 50])
        """

        try:
            await self.myvts.request(
                self.myvts.vts_request.requestSetMultiParameterValue(names, values)
            )
        except:
            await self.VTubeConnect()
            await self.myvts.request(
                self.myvts.vts_request.requestSetMultiParameterValue(names, values)
            )

    async def AddVariables(self):
        """
        Создаёт все нужные переменные
        """

        addparam = self.AddCustomParameter
        await addparam("EmiFaceAngleX")
        await addparam("EmiFaceAngleY")
        await addparam("EmiFaceAngleZ")
        await addparam("EmiEyeOpenLeft")
        await addparam("EmiEyeOpenRight")
        await addparam("EmiEyeX")
        await addparam("EmiEyeY")
        await addparam("EmiMountSmile")
        await addparam("EmiMountX")

class Emotes():
    """
    Все эмоции здесь
    """