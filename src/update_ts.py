import shutil
import subprocess
import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent

py_files = [str(p.resolve()) for p in (src_dir / "modules").rglob("*.py")]
if (src_dir / "main.py").exists():
    py_files.append(str((src_dir / "main.py").resolve()))

ts_files = [
    str(src_dir / "lang/de_DE.ts"),
    str(src_dir / "lang/es_ES.ts"),
    str(src_dir / "lang/pt_PT.ts"),
    str(src_dir / "lang/ru_RU.ts"),
    str(src_dir / "lang/uk_UA.ts"),
]

pylupdate_bin = shutil.which("pylupdate6") or str(Path(sys.executable).parent / "pylupdate6")
cmd = [pylupdate_bin, "--verbose", "--no-obsolete"] + py_files

for ts in ts_files:
    cmd += ["-ts", ts]

subprocess.run(cmd, check=False)
