@echo off
setlocal
echo === Build ImportadorXLS ===

REM --- PyInstaller ---
pyinstaller service.spec --noconfirm
if errorlevel 1 (
    echo ERRO no PyInstaller
    exit /b 1
)
echo Build do executavel concluido.

REM --- Inno Setup ---
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo Inno Setup nao encontrado em %ISCC%
    echo Instale o Inno Setup 6 ou ajuste o caminho no build.bat
    exit /b 1
)

if not exist "dist\installer" mkdir "dist\installer"
%ISCC% installer\installer.iss
if errorlevel 1 (
    echo ERRO no Inno Setup
    exit /b 1
)

echo.
echo === Build finalizado ===
echo Instalador gerado em: dist\installer\ImportadorXLS_Setup.exe
