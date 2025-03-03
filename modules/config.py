import os, json

def writeconfig(variable, value, configfile = "config.json"):
    try:
        with open(configfile, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError:
         data = {}
    data.update({variable: value})
    with open(configfile, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def getconfig(value, def_value = "", configfile = "config.json"):
    if os.path.exists(configfile):
        with open(configfile, "r", encoding="utf-8") as configfile:
            config = json.load(configfile)
            return config.get(value, def_value)
    else:
        return def_value

def writechardata(character, variable, value, char_data_file = "data.json"):
    try:
        with open(char_data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError:
         data = {}
    data[character][variable] = value
    with open(char_data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def getchardata(character, variable, char_data_file = "data.json"):
    if os.path.exists(char_data_file):
        with open(char_data_file, "r", encoding="utf-8") as char_data_file:
            data = json.load(char_data_file)
            character_data = data.get(character, None)
            if character_data:
                return  character_data.get(variable, None)
            else:
                return None
    else:
        return None

def exe_check():
    if os.path.exists("emilia.exe") and not os.path.exists("emilia.py"):
        return True
    else:
        return False