; installer.iss
[Setup]
AppName=ScanChecker
AppVersion=1.0
DefaultDirName={pf}\ScanChecker
DefaultGroupName=ScanChecker
OutputBaseFilename=ScanCheckerInstaller
Compression=lzma
SolidCompression=yes

[Files]
; Include built executable
Source: "dist\gui\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
; Run Tesseract installer silently after app install completes
Filename: "{tmp}\tesseract-ocr-w64-setup-5.5.0.20241111.exe"; Parameters: "\SILENT"; Flags: postinstall waituntilterminated shellexec runasoriginaluser

[Icons]
Name: "{group}\ScanChecker"; Filename: "{app}\gui.exe"