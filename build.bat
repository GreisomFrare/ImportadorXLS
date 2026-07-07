@echo off
setlocal
echo === Build ImportadorXLS ===

pyinstaller service.spec --noconfirm

if errorlevel 1 (
    echo ERRO no PyInstaller
    exit /b 1
)

echo Build concluido com sucesso.
