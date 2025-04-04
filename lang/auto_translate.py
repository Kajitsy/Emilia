import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator


def translate_ts(ts_file, output_ts, source_lang="ru", target_lang="pt"):
    tree = ET.parse(ts_file)
    root = tree.getroot()
    translator = GoogleTranslator(source=source_lang, target=target_lang)

    for context in root.findall("context"):
        for message in context.findall("message"):
            source = message.find("source").text or ""
            translation = message.find("translation")
            if translation is not None and translation.text:
                print(translation.text, end=", ")
                translation.text = translator.translate(translation.text)
                print(translation.text)

    tree.write(output_ts, encoding="utf-8", xml_declaration=True)
    print(f"Translated file saved to {output_ts}")


# Использование
translate_ts("ru_RU.ts", "pt_PT.ts")
