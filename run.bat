@echo off
IF NOT EXIST ".venv\Scripts\activate.bat" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py