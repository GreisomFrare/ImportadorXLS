@echo off
setlocal
set ORIGEM=%~dp0
set APP_DIR=C:\Viasoft\Client\PlugIns\ImportadorXLS
set CONFIG_DIR=C:\Viasoft\Client\PlugIns
set PLUGINS_DIR=C:\ViasoftTMS\Viasoft\Client\Plugins

echo === Instalando ImportadorXLS ===

REM Parar servico se ja existir
net stop ImportadorXLS 2>nul
"%APP_DIR%\ImportadorXLS.exe" remove 2>nul

REM Criar diretorios
if not exist "%APP_DIR%"     mkdir "%APP_DIR%"
if not exist "%CONFIG_DIR%"  mkdir "%CONFIG_DIR%"
if not exist "%PLUGINS_DIR%" mkdir "%PLUGINS_DIR%"

REM Copiar executavel
copy /y "%ORIGEM%ImportadorXLS.exe" "%APP_DIR%\" >nul
echo Executavel copiado.

REM Copiar arquivos do plugin ERP
copy /y "%ORIGEM%ImportadorXLS.conf" "%PLUGINS_DIR%\" >nul
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
net start ImportadorXLS
if errorlevel 1 (
    echo ERRO ao iniciar o servico.
    pause
    exit /b 1
)

echo.
echo Instalacao concluida! Reinicie o ERP para carregar o menu.
pause
