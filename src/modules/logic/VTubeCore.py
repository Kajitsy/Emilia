import json
import random

from pyvts import vts


class EEC:
    def __init__(self, main_window, host="127.0.0.1", port=8001):
        self.plugin_info = {
            "plugin_name": "Emilia Next",
            "developer": "Kajitsy",
            "authentication_token_path": "./data/VTube_Token.txt",
        }
        self.vts_api_info = {
            "host": host,
            "name": "VTubeStudioPublicAPI",
            "port": port,
            "version": "1.0",
        }

        self.vts = vts(self.plugin_info, self.vts_api_info)
        self.mw = main_window

    def create_vts_with_port(self, port):
        self.vts_api_info["port"] = port
        self.vts = vts(self.plugin_info, self.vts_api_info)

    def set_port(self, port):
        self.vts_api_info["port"] = port
        self.vts = vts(self.plugin_info, self.vts_api_info)

    def set_host(self, host):
        self.vts_api_info["host"] = host
        self.vts = vts(self.plugin_info, self.vts_api_info)

    async def connect(self):
        await self.vts.connect()
        try:
            await self.vts.read_token()
            await self.vts.request_authenticate()
        except Exception:
            await self.vts.request_authenticate_token()
            await self.vts.write_token()
            await self.vts.request_authenticate()

    async def close(self):
        await self.vts.close()

    async def UseEmote(self, emote):
        with open("./data/VTube_Emotes.json", "r", encoding="utf-8") as f:
            emotes_data = json.load(f)

        emote_data = emotes_data[emote]["params"]
        rndm = random.randint
        names = []
        values = []
        for parameter_name, parameter_value in emote_data.items():
            parameter_value = str(parameter_value)
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

        for i, name in enumerate(names):
            value = values[i]
            await self.vts.request(
                self.vts.vts_request.requestCustomParameter(
                    parameter=name, min=0, max=100, default_value=int(value)
                )
            )
