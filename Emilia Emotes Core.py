import pyvts

class EMC():
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

    async def CustomParameter(self, name, value=0, min=-100, max=100):
        """
        Лучше всего использовать для создания параметров плагина\n

        CustomParameter("EmiEyeX", -100, 100, 0)
        """
        try:
            await self.myvts.request(
                self.myvts.vts_request.requestCustomParameter(name, min, max, value)
            )
        except:
            await EMC().vtubeconnect()
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
            await EMC().vtubeconnect()
            await self.myvts.request(
                self.myvts.vts_request.requestSetMultiParameterValue(names, values)
            )

    async def GetParameterValue(self, name):
        """
        Нужно для получение значения переменной в VTube Studio\n

        GetParameterValue("EmiEyeX")
        """
        try:
            await self.myvts.request(
                self.myvts.vts_request.requestParameterValue(name)
            )
        except:
            await EMC().vtubeconnect()
            await self.myvts.request(
                self.myvts.vts_request.requestParameterValue(name)
            )