@echo off
echo Запуск интернет-магазина...
echo.

:: Активация виртуального окружения
call venv\Scripts\activate.bat

:: Запуск приложения
python app.py

pause