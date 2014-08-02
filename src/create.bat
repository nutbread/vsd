:: ============================================================================
:: Virtual SD card (re)creation script
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

set BATCH_FULL_FILENAME=%0
for %%A in ("%BATCH_FULL_FILENAME%") do (
    set BATCH_PATH=%%~dpA
    set BATCH_FILENAME=%%~nxA
)



:: ============================================================================
:: Check for python
:: ============================================================================

"%PYTHON%" --version > NUL 2> NUL || goto :error_no_python

:: ============================================================================
:: Delete required?
:: ============================================================================

set DELETE_COMMAND=

if not exist "%SD_CARD_PATH%" goto :question_end
:question_ask
echo The virtual SD card file already exists.
set /P QUESTION="Do you want to delete it and create a new one? (Y/N) " || goto :question_no

if /i "%QUESTION%"=="YES" goto :question_yes
if /i "%QUESTION%"=="Y" goto :question_yes

:question_no
echo The virtual sd card will not be re-created.
if %NO_PAUSE%==0 (
	color 0c
	pause > NUL 2> NUL
	color
)
goto :eof

:question_yes
set DELETE_COMMAND=--delete

:question_end



:: ============================================================================
:: Create
:: ============================================================================

"%PYTHON%" vsd.py ^
	--path "%SD_CARD_PATH%" ^
	--size "%SD_CARD_SIZE%" ^
	--file-system "%SD_CARD_FILE_SYSTEM%" ^
	%DELETE_COMMAND% ^
	--create ^
	|| goto :error



:: ============================================================================
:: Success
:: ============================================================================

"%PYTHON%" shortcut.py ^
	--filename "%SHORTCUT_TO_DIRECTORY_FILENAME%" ^
	--target "%SD_CARD_PATH_BASE%." ^
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

