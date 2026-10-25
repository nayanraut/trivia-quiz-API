@echo off
title Trivia Master (OpenTDB)
cd /d "%~dp0"

echo ========================================================
echo        TRIVIA MASTER - Open Trivia Database
echo ========================================================
echo.
echo Choose an option:
echo   [1] Launch Desktop GUI (Default - Category Selection Available)
echo   [2] Launch CLI: Science: Mathematics (50 Questions)
echo   [3] Launch CLI: Science: Gadgets (34 Questions)
echo   [4] Launch CLI: Sudden Death Survival (Gadgets)
echo   [5] Refresh Questions from OpenTDB
echo   [6] Exit
echo.

set /p choice="Enter choice [1-6] (default 1): "

if "%choice%"=="" set choice=1
if "%choice%"=="1" goto gui
if "%choice%"=="2" goto cli_math
if "%choice%"=="3" goto cli_gadgets
if "%choice%"=="4" goto cli_survival_gadgets
if "%choice%"=="5" goto refresh
if "%choice%"=="6" goto end

:gui
where py >nul 2>nul
if %errorlevel%==0 (
    py main.py
) else (
    python main.py
)
goto end

:cli_math
where py >nul 2>nul
if %errorlevel%==0 (
    py main.py --cli --category math --mode marathon
) else (
    python main.py --cli --category math --mode marathon
)
pause
goto end

:cli_gadgets
where py >nul 2>nul
if %errorlevel%==0 (
    py main.py --cli --category gadgets --mode marathon
) else (
    python main.py --cli --category gadgets --mode marathon
)
pause
goto end

:cli_survival_gadgets
where py >nul 2>nul
if %errorlevel%==0 (
    py main.py --cli --category gadgets --mode survival
) else (
    python main.py --cli --category gadgets --mode survival
)
pause
goto end

:refresh
where py >nul 2>nul
if %errorlevel%==0 (
    py main.py --refresh --category gadgets
    py main.py --refresh --category math
) else (
    python main.py --refresh --category gadgets
    python main.py --refresh --category math
)
pause
goto end

:end
