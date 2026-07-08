@echo off
echo Instalando servico ImportadorXLS...
python service.py install
if errorlevel 1 (
    echo ERRO ao instalar o servico
    pause
    exit /b 1
)
net start ImportadorXLS
echo Servico instalado e iniciado.
pause
