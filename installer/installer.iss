[Setup]
AppName=ImportadorXLS
AppVersion=1.0.0
AppPublisher=Viasoft
DefaultDirName=C:\Viasoft\Client\PlugIns\ImportadorXLS
DefaultGroupName=Viasoft\ImportadorXLS
OutputDir=dist\installer
OutputBaseFilename=ImportadorXLS_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "dist\ImportadorXLS.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer\ImportadorXLS.jvpi"; DestDir: "C:\ViasoftTMS\Viasoft\Client\Plugins"; Flags: ignoreversion
Source: "installer\ImportadorXLS.conf"; DestDir: "C:\ViasoftTMS\Viasoft\Client\Plugins"; Flags: ignoreversion

[Run]
Filename: "{app}\ImportadorXLS.exe"; Parameters: "install"; StatusMsg: "Instalando servi�o..."; Flags: runhidden
Filename: "net"; Parameters: "start ImportadorXLS"; StatusMsg: "Iniciando servi�o..."; Flags: runhidden

[UninstallRun]
Filename: "net"; Parameters: "stop ImportadorXLS"; Flags: runhidden
Filename: "{app}\ImportadorXLS.exe"; Parameters: "remove"; Flags: runhidden

[Code]
procedure CreateDefaultConfig();
var
  ConfigDir: string;
  ConfigPath: string;
  ConfigContent: string;
begin
  ConfigDir := 'C:\Viasoft\Client\PlugIns';
  ConfigPath := ConfigDir + '\importadorxls_config.json';
  if not DirExists(ConfigDir) then
    CreateDir(ConfigDir);
  if not FileExists(ConfigPath) then
  begin
    ConfigContent := '{"oracle":{"modo_conexao":"DIRETO","usuario":"","senha":"",' +
                     '"direto":{"host":"","porta":1521,"sid":"","service_name":""},' +
                     '"tns":{"alias":"","tnsnames_path":"","oracle_client_bin":""}},' +
                     '"server":{"porta":5002}}';
    SaveStringToFile(ConfigPath, ConfigContent, False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    CreateDefaultConfig();
end;
