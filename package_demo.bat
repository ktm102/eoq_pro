@echo off
setlocal ENABLEDELAYEDEXPANSION
title EOQ Pro — Packaging demo (Windows, no source in ZIP)
set "ROOT=%~dp0"
pushd "%ROOT%" >nul
set "APP_NAME=EOQ_Pro"
set "BIN_NAME=EOQ_Pro"
set "OUT_DIR=EOQ_Pro_Demo"
set "ZIP_NAME=eoq_pro_windows.zip"
echo == EOQ Pro: Packaging demo (Windows) ==
echo Cartella script: %ROOT%

if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
if exist "%OUT_DIR%" rmdir /s /q "%OUT_DIR%"
if exist "%ZIP_NAME%" del "%ZIP_NAME%"

where pyinstaller >nul 2>nul
if errorlevel 1 (
  echo ERRORE: PyInstaller non trovato. Installa con: pip install pyinstaller
  goto :END
)

if /i "%SKIP_BUILD%"=="1" (
  echo Salto build (SKIP_BUILD=1). Uso exe esistente in dist\ ...
) else (
  set "ICONOPT="
  if exist "app.ico" set "ICONOPT=--icon app.ico"
  set "VEROPT="
  if exist "version_info.txt" set "VEROPT=--version-file version_info.txt"
  set "KEYOPT="
  if not "%PYI_KEY%"=="" set "KEYOPT=--key %PYI_KEY%"
  echo Compilo con PyInstaller...
  pyinstaller --noconsole --onefile --name "%BIN_NAME%" %ICONOPT% %VEROPT% %KEYOPT% "eoq_pro.py"
  if errorlevel 1 (
    echo ERRORE: compilazione PyInstaller fallita.
    goto :END
  )
)

mkdir "%OUT_DIR%"
if exist "dist\%BIN_NAME%.exe" copy /y "dist\%BIN_NAME%.exe" "%OUT_DIR%\" >nul
if exist "Guida_EOQ_Pro_Semplice_compact.pdf" copy /y "Guida_EOQ_Pro_Semplice_compact.pdf" "%OUT_DIR%\Guida_EOQ_Pro.pdf" >nul
if exist "Guida_EOQ_Pro_Semplice.txt" copy /y "Guida_EOQ_Pro_Semplice.txt" "%OUT_DIR%\Guida_EOQ_Pro.txt" >nul
if exist "README_EOQ_Pro_Semplice.md" copy /y "README_EOQ_Pro_Semplice.md" "%OUT_DIR%\README.md" >nul
if exist "EULA.txt" copy /y "EULA.txt" "%OUT_DIR%\" >nul
if exist "Privacy_Policy.txt" copy /y "Privacy_Policy.txt" "%OUT_DIR%\" >nul
if exist "eoq_demo_sample.csv" copy /y "eoq_demo_sample.csv" "%OUT_DIR%\" >nul
if exist "brand_logo.svg" copy /y "brand_logo.svg" "%OUT_DIR%\" >nul
if exist "VERSION" copy /y "VERSION" "%OUT_DIR%\" >nul

powershell -NoProfile -Command "Compress-Archive -Path '%OUT_DIR%\*' -DestinationPath '%ZIP_NAME%' -Force" || (
  echo ERRORE: creazione ZIP fallita.
  goto :END
)

powershell -NoProfile -Command ^
  "$z=[IO.Compression.ZipFile]::OpenRead('%ZIP_NAME%');$bad=$false;foreach($e in $z.Entries){if($e.FullName.ToLower().EndsWith('.py')){$bad=$true;Write-Host 'Trovato sorgente nello ZIP:' $e.FullName}};$z.Dispose();if($bad){exit 1}else{Write-Host 'Verifica OK: nessun .py nello ZIP.'}"

if errorlevel 1 (
  echo ERRORE: nello ZIP ci sono file .py. Interrompo.
  goto :END
)

echo.
echo Completato: %ZIP_NAME%
echo Posizione: %ROOT%%ZIP_NAME%

:END
popd >nul
endlocal
