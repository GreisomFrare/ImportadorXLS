@echo off
set APP_DIR=C:\Viasoft\Client\PlugIns\ImportadorXLS

echo === Desinstalando ImportadorXLS ===

net stop ImportadorXLS 2>nul
"%APP_DIR%\ImportadorXLS.exe" remove
if errorlevel 1 (
    echo ERRO ao remover o servico.
    pause
    exit /b 1
)

echo Servico removido. Os arquivos em %APP_DIR% foram mantidos.
pause
