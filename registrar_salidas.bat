@echo off
REM Script para registrar salidas automáticas a las 4:00 PM
REM Este script debe configurarse en el Programador de Tareas de Windows

cd /d E:\Escuela_backup\Escuela
call .venv\Scripts\activate.bat
python manage.py registrar_salidas_automaticas

REM Opcional: Registrar en log
REM python manage.py registrar_salidas_automaticas >> logs\salidas_automaticas.log 2>&1
