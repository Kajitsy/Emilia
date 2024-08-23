import sys, os, json

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def writeconfig(variable, value, configfile = 'config.json'):
    try:
        with open(configfile, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError:
         data = {}
    data.update({variable: value})
    with open(configfile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def getconfig(value, def_value = "", configfile = 'config.json'):
    if os.path.exists(configfile):
        with open(configfile, 'r') as configfile:
            config = json.load(configfile)
            return config.get(value, def_value)
    else:
        return def_value