:: ============================================================================
:: Virtual SD card mount script
:: ============================================================================
@echo off
cls



:: ============================================================================
:: Setup
:: ============================================================================

call settings.bat

set NO_PAUSE=0
if "%1%"=="-p" set NO_PAUSE=1
if "%1%"=="--no-pause" set NO_PAUSE=1

set BATCH_FULL_FILENAME=build.bat
for %%A in ("%BATCH_FULL_FILENAME%") do (
    set BATCH_PATH=%%~dpA
    set BATCH_FILENAME=%%~nxA
)



:: ============================================================================
:: Check for python
:: ============================================================================

"%PYTHON%" --version > NUL 2> NUL || goto :error_no_python

:: ============================================================================
:: Mount
:: ============================================================================

"%PYTHON%" vsd.py ^
	--path "%SD_CARD_PATH%" ^
	--letter "%SD_CARD_MOUNT_DRIVE_LETTER%" ^
	--mount ^
	|| goto :error



:: ============================================================================
:: Success
:: ============================================================================

"%PYTHON%" shortcut.py ^
	--filename "%SHORTCUT_TO_DRIVE_FILENAME%" ^
	--target "%SD_CARD_MOUNT_DRIVE_LETTER%:\." ^
	> NUL 2> NUL

goto :eof

:: ============================================================================
:: Execution error
:: ============================================================================
:error
if %NO_PAUSE%==0 (
	color 0c
	pause > NUL 2> NUL
	color
)
goto :eof



:: ============================================================================
:: No python error
:: ============================================================================
:error_no_python
if %NO_PAUSE%==0 color 0c
call settings.bat error_no_python
if %NO_PAUSE%==0 (
	pause > NUL 2> NUL
	color
)
goto :eof

