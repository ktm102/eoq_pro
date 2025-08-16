@echo off
setlocal enableextensions enabledelayedexpansion

REM ===== EOQ Pro: Packaging demo (Windows) =====
set "APP_NAME_DIR=EOQ_Pro_Demo"
set "OUT_BASENAME=eoq_pro_demo"
set "BIN_NAME=EOQ_Pro"

REM 0) Vai nella cartella dello script
pushd "%~dp0"

echo(
echo == EOQ Pro: Packaging demo (Windows) ==
echo Cartella script: %CD%
echo(

REM ===== versione =====
set "VERSION=%VERSION%"
if "%VERSION%"=="" (
  if exist VERSION (
    set /p VERSION=<VERSION
  ) else (
    set "VERSION=1.0.0"
  )
)
set "OUT_ZIP=%OUT_BASENAME%_v%VERSION%.zip"
echo Versione: %VERSION%

REM 1) Controllo file essenziali
if not exist "eoq_pro.py" (
  echo ERRORE: eoq_pro.py non trovato nella cartella corrente.
  echo Apri una finestra di Prompt in questa cartella e riprova.
  goto :end
)
if not exist "EULA.txt" echo AVVISO: EULA.txt non trovato - continuo.
if not exist "Privacy_Policy.txt" echo AVVISO: Privacy_Policy.txt non trovato - continuo.
if not exist "Guida_EOQ_Pro_Semplice.txt" echo AVVISO: Guida_EOQ_Pro_Semplice.txt non trovata - continuo.
if not exist "README_EOQ_Pro_Semplice.md" echo AVVISO: README_EOQ_Pro_Semplice.md non trovato - continuo.
if not exist "eoq_demo_sample.csv" echo AVVISO: eoq_demo_sample.csv non trovato - continuo.
if not exist "brand_logo.svg" echo AVVISO: brand_logo.svg non trovato - continuo.

REM 2) (Opzionale) Build con PyInstaller se installato e non saltato
where pyinstaller >nul 2>&1
if %errorlevel%==0 (
  if "%SKIP_BUILD%"=="1" (
    echo Build PyInstaller saltata [SKIP_BUILD=1].
  ) else (
    set "ADDDATA="
    if exist "brand_logo.svg" set "ADDDATA=--add-data ""brand_logo.svg;."""
    echo Trovato PyInstaller. Compilo l'eseguibile...
    pyinstaller --noconsole --onefile --name "%BIN_NAME%" %ADDDATA% "eoq_pro.py"
    if errorlevel 1 (
      echo ERRORE: compilazione PyInstaller fallita. Continuo senza eseguibile.
    ) else (
      echo Build completata. Output in .\dist
    )
  )
) else (
  echo PyInstaller non trovato. Procedo senza eseguibile.
)

REM 3) Prepara cartella demo
if exist "%APP_NAME_DIR%" rmdir /s /q "%APP_NAME_DIR%"
mkdir "%APP_NAME_DIR%"

REM 4) Copia file essenziali
copy /y "eoq_pro.py" "%APP_NAME_DIR%\" >nul
if exist "Guida_EOQ_Pro_Semplice.txt" copy /y "Guida_EOQ_Pro_Semplice.txt" "%APP_NAME_DIR%\Guida_EOQ_Pro.txt" >nul
if exist "README_EOQ_Pro_Semplice.md" copy /y "README_EOQ_Pro_Semplice.md" "%APP_NAME_DIR%\README.md" >nul
if exist "EULA.txt" copy /y "EULA.txt" "%APP_NAME_DIR%\" >nul
if exist "Privacy_Policy.txt" copy /y "Privacy_Policy.txt" "%APP_NAME_DIR%\" >nul
if exist "eoq_demo_sample.csv" copy /y "eoq_demo_sample.csv" "%APP_NAME_DIR%\" >nul
if exist "brand_logo.svg" copy /y "brand_logo.svg" "%APP_NAME_DIR%\" >nul
if exist "VERSION" copy /y "VERSION" "%APP_NAME_DIR%\" >nul

REM 5) Copia l'eseguibile se presente
if exist "dist\%BIN_NAME%.exe" (
  copy /y "dist\%BIN_NAME%.exe" "%APP_NAME_DIR%\" >nul
  echo Incluso eseguibile: %BIN_NAME%.exe
) else (
  if exist "dist\%BIN_NAME%" (
    copy /y "dist\%BIN_NAME%" "%APP_NAME_DIR%\" >nul
    echo Incluso eseguibile: %BIN_NAME%
  ) else (
    echo Nessun eseguibile trovato in dist^/ - ok per demo solo-Python.
  )
)

REM 6) Avvio rapido (niente blocchi con parentesi; escape delle parentesi)
> "%APP_NAME_DIR%\AVVIO_RAPIDO.txt" echo Avvio rapido:
>> "%APP_NAME_DIR%\AVVIO_RAPIDO.txt" echo - Se trovi l'eseguibile EOQ_Pro.exe: fai doppio clic.
>> "%APP_NAME_DIR%\AVVIO_RAPIDO.txt" echo - Altrimenti ^(versione Python^):
>> "%APP_NAME_DIR%\AVVIO_RAPIDO.txt" echo   1^) Apri il Prompt in questa cartella
>> "%APP_NAME_DIR%\AVVIO_RAPIDO.txt" echo   2^) Esegui:  python eoq_pro.py
>> "%APP_NAME_DIR%\AVVIO_RAPIDO.txt" echo Opzionali: pip install matplotlib reportlab

REM 7) Crea ZIP versionato + alias non versionato
if exist "%OUT_ZIP%" del "%OUT_ZIP%"
if exist "%OUT_BASENAME%.zip" del "%OUT_BASENAME%.zip"

echo Creo ZIP con PowerShell...
powershell -NoProfile -Command "Compress-Archive -Path '%APP_NAME_DIR%\*' -DestinationPath '%OUT_ZIP%' -Force"
if errorlevel 1 (
  echo PowerShell Compress-Archive fallito. Provo con tar...
  tar -a -c -f "%OUT_ZIP%" "%APP_NAME_DIR%" 2>nul
  if errorlevel 1 (
    echo ERRORE: impossibile creare lo ZIP. Installa PowerShell 5+ oppure 7-Zip.
    goto :writechangelog
  ) else (
    echo Creato %OUT_ZIP% con tar.
  )
) else (
  echo Creato %OUT_ZIP% con PowerShell.
)

copy /y "%OUT_ZIP%" "%OUT_BASENAME%.zip" >nul

:writechangelog
REM 8) Aggiorna CHANGELOG.md
set "NOW=%date% %time%"
if not exist CHANGELOG.md echo # Changelog>CHANGELOG.md
>>CHANGELOG.md echo ## v%VERSION% — %NOW%
>>CHANGELOG.md echo - Pacchetto demo generato (^%OUT_ZIP^%)
>>CHANGELOG.md echo - Include: app Python, ^(eventuale^) eseguibile, guida/README ^(se presenti^), EULA, privacy, CSV di esempio, VERSION
>>CHANGELOG.md echo.

echo(
echo == Operazione completata. ==
echo ZIP: %OUT_ZIP%  (e alias %OUT_BASENAME%.zip)
echo Contenuto cartella: %APP_NAME_DIR%
echo(

:end
echo Premere un tasto per chiudere...
pause >nul
popd
endlocal
