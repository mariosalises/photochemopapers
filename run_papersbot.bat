@echo off
cd /d D:\PhotoChemoPapers\PapersBot
call venv\Scripts\activate.bat
python papersbot.py >> logs\papersbot.log 2>&1