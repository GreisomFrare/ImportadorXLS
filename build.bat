@echo off
setlocal
echo === Build ImportadorXLS ===

REM --- Gerar executavel ---
pyinstaller service.spec --noconfirm
if errorlevel 1 (
    echo ERRO no PyInstaller
    pause
    exit /b 1
)

REM --- Montar pacote de distribuicao ---
if exist "dist\package" rmdir /s /q "dist\package"
mkdir "dist\package"

copy /y "dist\ImportadorXLS.exe"             "dist\package\"
copy /y "installer\ImportadorXLS.conf"        "dist\package\"
copy /y "installer\ImportadorXLS.jvpi"        "dist\package\"
copy /y "installer\instalar.bat"              "dist\package\"
copy /y "installer\desinstalar.bat"           "dist\package\"

REM Config padrao (nao sobrescreve se ja existir no cliente)
echo {"oracle":{"modo_conexao":"DIRETO","usuario":"","senha":"","direto":{"host":"","porta":1521,"sid":"","service_name":""},"tns":{"alias":"","tnsnames_path":"","oracle_client_bin":""}},"server":{"porta":5002}} > "dist\package\importadorxls_config.json"

echo.
echo Pacote gerado em: dist\package\
echo Compacte a pasta dist\package\ e entregue ao cliente.
pause
