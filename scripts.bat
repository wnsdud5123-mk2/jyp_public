@echo off
py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconsole --onefile ^
  --add-data "hum.jpg;." ^
  app.py
echo.
echo Build done. See dist\app.exe
pause
