@echo Loading libraries... 
@echo off
pip install speechrecognition
pip install setuptools
pip install characterai
pip install sounddevice
pip install soundfile
pip install pyvts
pip install pyaudio
pip install numpy<2
pip install PyQt6
@echo Emilia Launch
python emilia_charai.py
pause
@echo Press any key to continue. . .