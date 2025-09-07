@echo off
setlocal

:: === Configuração de caminhos ===
set "ROOT=%~dp0"
set "LOGDIR=%ROOT%logs"
set "LOGFILE=%LOGDIR%\skoob-sync.log"

:: === Garante que a pasta de log existe ===
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

:: === Limpa arquivo se quiser sobrescrever cada vez (opcional) ===
:: echo. > "%LOGFILE%"

:: === Carimbo de início ===
>>"%LOGFILE%" echo ================================
>>"%LOGFILE%" echo INÍCIO (%date% %time%)
>>"%LOGFILE%" echo ================================

:: === Setup do Python ===
set "SYS_PY=py"
set "VENV_DIR=%ROOT%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

>>"%LOGFILE%" echo [INFO] Raiz: %ROOT%
>>"%LOGFILE%" echo [INFO] Venv: %PYTHON_EXE%

if not exist "%PYTHON_EXE%" (
    >>"%LOGFILE%" echo [INFO] Venv nao encontrado. Criando...
    %SYS_PY% -m venv "%VENV_DIR%" >>"%LOGFILE%" 2>&1
    if errorlevel 1 (
        >>"%LOGFILE%" echo [ERRO] Falha ao criar venv.
        goto :FIM
    )
    >>"%LOGFILE%" echo [INFO] Venv criado com sucesso.
) else (
    >>"%LOGFILE%" echo [INFO] Venv existente.
)

>>"%LOGFILE%" echo [INFO] Instalando dependencias...
"%PYTHON_EXE%" -m pip install -r "%ROOT%requirements.txt" >>"%LOGFILE%" 2>&1
if errorlevel 1 (
    >>"%LOGFILE%" echo [ERRO] Falha ao instalar dependencias.
    goto :FIM
)

>>"%LOGFILE%" echo [INFO] Executando script Python...
"%PYTHON_EXE%" "%ROOT%skoob-automator.py" >>"%LOGFILE%" 2>&1
set "RC=%ERRORLEVEL%"
>>"%LOGFILE%" echo [INFO] Script finalizado. RC=%RC%

:FIM
>>"%LOGFILE%" echo ================================
>>"%LOGFILE%" echo FIM (%date% %time%) RC=%RC%
>>"%LOGFILE%" echo ================================
endlocal & exit /b %RC%
