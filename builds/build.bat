:: ============================================================================
:: .zip package builder
:: ============================================================================
@echo off

:: Set output filename
set OUTPUT_FILE=%~dp0%build_package.zip

:: Delete
del "%OUTPUT_FILE%" > NUL 2> NUL

:: Compress
7z.exe a -tzip -mx=9 -mtc=off "%OUTPUT_FILE%" "..\src\*.py" "..\src\*.bat"
