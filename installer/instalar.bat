@echo off
setlocal enabledelayedexpansion
set ORIGEM=%~dp0
set APP_DIR=C:\Viasoft\Client\PlugIns\ImportadorXLS
set CONFIG_DIR=C:\Viasoft\Client\PlugIns
set PLUGINS_DIR=C:\Viasoft\Client\PlugIns

echo === Instalando ImportadorXLS ===

REM Parar servico se ja existir
net stop ImportadorXLS 2>nul

REM Aguardar o processo parar completamente antes de remover
:aguardar_parada
sc query ImportadorXLS 2>nul | find "STOPPED" >nul
if not errorlevel 1 goto remover_servico
sc query ImportadorXLS 2>nul | find "SERVICE_NAME" >nul
if errorlevel 1 goto remover_servico
timeout /t 2 /nobreak >nul
goto aguardar_parada

:remover_servico
"%APP_DIR%\ImportadorXLS.exe" remove 2>nul

REM Aguardar o SCM liberar o servico (evita erro 1072)
:aguardar_remocao
sc query ImportadorXLS 2>nul | find "SERVICE_NAME" >nul
if errorlevel 1 goto criar_dirs
timeout /t 2 /nobreak >nul
goto aguardar_remocao

:criar_dirs
REM Criar diretorios
if not exist "%APP_DIR%"     mkdir "%APP_DIR%"
if not exist "%CONFIG_DIR%"  mkdir "%CONFIG_DIR%"
if not exist "%PLUGINS_DIR%" mkdir "%PLUGINS_DIR%"

REM Copiar executavel (com retry caso o processo anterior ainda esteja liberando o arquivo)
copy /y "%ORIGEM%ImportadorXLS.exe" "%APP_DIR%\" >nul
if errorlevel 1 (
    echo Arquivo em uso, aguardando liberacao...
    timeout /t 5 /nobreak >nul
    copy /y "%ORIGEM%ImportadorXLS.exe" "%APP_DIR%\" >nul
    if errorlevel 1 (
        echo ERRO ao copiar executavel.
        pause
        exit /b 1
    )
)
echo Executavel copiado.

REM Gerar arquivo .conf somente se nao existir
if not exist "%PLUGINS_DIR%\ImportadorXLS.conf" (
    REM Descobrir porta configurada (usa 5002 se config nao existir ainda)
    set PORTA=5002
    if exist "%CONFIG_DIR%\importadorxls_config.json" (
        for /f "usebackq delims=" %%p in (`powershell -NoProfile -Command "try{(Get-Content '%CONFIG_DIR%\importadorxls_config.json' -Raw | ConvertFrom-Json).server.porta}catch{5002}"`) do set PORTA=%%p
    )
    (
        echo [cfg]
        echo AppName=FinAgro3c
        echo MenuAction=Integracoes
        echo Caption=Importador XLS
        echo URL=http://%COMPUTERNAME%:!PORTA!/index.html
    ) > "%PLUGINS_DIR%\ImportadorXLS.conf"
    echo Arquivo .conf criado ^(URL: http://%COMPUTERNAME%:!PORTA!/index.html^).
) else (
    echo Arquivo .conf existente mantido.
)
copy /y "%ORIGEM%ImportadorXLS.jvpi" "%PLUGINS_DIR%\" >nul
echo Arquivos do plugin ERP copiados.

REM Copiar config padrao somente se nao existir
if not exist "%CONFIG_DIR%\importadorxls_config.json" (
    copy /y "%ORIGEM%importadorxls_config.json" "%CONFIG_DIR%\" >nul
    echo Arquivo de configuracao criado. Configure a conexao Oracle pelo sistema.
) else (
    echo Configuracao existente mantida.
)

REM Instalar e iniciar servico Windows
"%APP_DIR%\ImportadorXLS.exe" install
if errorlevel 1 (
    echo ERRO ao instalar o servico.
    pause
    exit /b 1
)

REM Configurar inicio automatico com delay (Automatic Delayed Start)
sc config ImportadorXLS start= delayed-auto >nul

net start ImportadorXLS
if errorlevel 1 (
    echo ERRO ao iniciar o servico.
    pause
    exit /b 1
)

echo.
echo Instalacao concluida! Reinicie o ERP para carregar o menu.
pause
