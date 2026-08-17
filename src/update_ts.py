import subprocess
from pathlib import Path

py_files = [str(p.resolve()) for p in Path("modules").rglob("*.py")]
py_files.append(str(Path("main.py").resolve()))

ts_files = [
    "lang/de_DE.ts",
    "lang/es_ES.ts",
    "lang/pt_PT.ts",
    "lang/ru_RU.ts",
    "lang/uk_UA.ts",
]
cmd = ["pylupdate6", "--verbose", "--no-obsolete"] + py_files

for ts in ts_files:
    cmd += ["-ts", ts]

subprocess.run(cmd, check=False)
