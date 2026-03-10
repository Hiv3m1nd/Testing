@echo off
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name DarkstoneKeep src\main.py

echo Build complete. EXE is in dist\DarkstoneKeep.exe
