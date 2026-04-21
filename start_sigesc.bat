@echo off
title SIGEsc - Servidor Django (Nginx + Waitress)
color 1F

REM --- Caminhos  ---
set PROJECT_DIR=C:\projectos\sigesc
set NGINX_DIR=C:\nginx-1.28.1
set PYTHON_SCRIPT=server.py

REM --- Inicia o Nginx ---
cd /d "%NGINX_DIR%"
echo Iniciando Nginx...
start nginx.exe
if errorlevel 1 (
    echo ERRO: Nao foi possivel iniciar o Nginx.
    pause
    exit /b 1
)

REM --- Inicia o Waitress (Django) ---
cd /d "%PROJECT_DIR%"
echo Iniciando Django com Waitress...
start python "%PYTHON_SCRIPT%"

REM --- Mensagem final ---
echo.
echo SIGEsc iniciado com sucesso!
echo Acesse em: http://192.168.2.102
echo.
pause