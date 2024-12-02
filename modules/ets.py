import json

class translations:
    def __init__(self, lang, folder="locales"):
        self.lang = lang
        self.folder = folder
        self.translations = self.load_translations(f"{folder}/{lang}.json")
        self.slang = self.translations["small"]

    def load_translations(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            with open(f"{self.folder}/en_US.json", "r", encoding="utf-8") as f:
                return json.load(f)

    def tr(self, context, text):
        if context in self.translations and text in self.translations[context]:
            return self.translations[context][text]
        else:
            return text