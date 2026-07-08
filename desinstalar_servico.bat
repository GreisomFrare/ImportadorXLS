@echo off
echo Parando e removendo servico ImportadorXLS...
net stop ImportadorXLS 2>nul
python service.py remove
if errorlevel 1 (
    echo ERRO ao remover o servico
    pause
    exit /b 1
)
echo Servico removido com sucesso.
pause
