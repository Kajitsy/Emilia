import json

class translations:
    def __init__(self, lang, folder="locales"):
        self.lang = lang
        self.folder = folder
        self.translations = self.load_translations(f"{folder}/{lang}.json")
        self.en_translations = self.load_translations(f"{folder}/en_US.json")
        self.slang = self.translations["small"]
        self.en_slang = self.en_translations["small"]

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
        elif context in self.en_translations and text in self.en_translations[context]:
            return self.en_translations[context][text]
        else:
            return text