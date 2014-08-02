@echo off



:: ============================================================================
:: Editable settings
:: ============================================================================

:: Path to the python.exe used execute the various scripts
set PYTHON=python

:: The label of the virtual SD card
set SD_CARD_LABEL=Label

:: The path to where the virtual SD card file should be created
set SD_CARD_PATH=sd.raw

:: The drive letter the card should be mounted to (for the default example, it would be "Q:\")
set SD_CARD_MOUNT_DRIVE_LETTER=Q

:: The size (in MiB) of the virtual SD card
set SD_CARD_SIZE=512

:: The file system of the virtual SD card
set SD_CARD_FILE_SYSTEM=FAT32




:: ============================================================================
:: Don't edit
:: ============================================================================

for %%A in ("%SD_CARD_PATH%") do (
    set SD_CARD_PATH_BASE=%%~dpA
    set SD_CARD_PATH_FILE=%%~nxA
)

set SHORTCUT_TO_DIRECTORY_FILENAME=%SD_CARD_PATH_FILE% Directory.lnk
set SHORTCUT_TO_DRIVE_FILENAME=%SD_CARD_PATH_FILE% Drive.lnk



:: ============================================================================
:: Additional code
:: ============================================================================
if "%1" NEQ "" call :%1
goto :eof



:: ============================================================================
:: No python error
:: ============================================================================
:error_no_python
echo The python.exe version check failed.
echo.
echo.
echo The most likely problem is that you do not have python installed,
echo   or python is not in your path environment variable.
echo.
echo.
echo If you have python installed, either:
echo   - Edit %BATCH_FILENAME%'s "PYTHON" setting at the top of the file;
echo     change it to the full path of where python.exe is installed
echo   or
echo   - Add python to your path environment variable (google how to do this)
echo.
echo.
echo If you don't have python, install it from the following link:
echo   https://www.python.org/
echo   (any up-to-date version should work)

goto :eof


