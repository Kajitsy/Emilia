@echo Loading libraries... 
@echo off
pip install speechrecognition
pip install setuptools
pip install characterai
pip install sounddevice
pip install soundfile
pip install gpytranslate
pip install pyvts
pip install pyaudio
pip install google-generativeai
pip install num2words
pip install numpy<2
pip install PyQt6
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
@echo Emilia Launch
python emilia.py
pause
@echo Press any key to continue. . .