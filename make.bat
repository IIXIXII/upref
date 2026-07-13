@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "VENV_PYTHON=%ROOT%.venv\Scripts\python.exe"
set "BOOTSTRAP=%ROOT%scripts\bootstrap.ps1"
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

cd /d "%ROOT%"

if "%~1"=="" goto action_help
if /i "%~1"=="setup" goto action_setup
if /i "%~1"=="test" goto action_test
if /i "%~1"=="check" goto action_check
if /i "%~1"=="docs" goto action_docs
if /i "%~1"=="build" goto action_build
if /i "%~1"=="clean" goto action_clean
if /i "%~1"=="help" goto action_help
if /i "%~1"=="-h" goto action_help
if /i "%~1"=="--help" goto action_help

>&2 echo Unknown action: %~1
set "HELP_EXIT_CODE=2"
goto print_help

:action_setup
if not exist "%BOOTSTRAP%" (
    >&2 echo Bootstrap script not found: "%BOOTSTRAP%"
    exit /b 1
)
if "%~2"=="" goto action_setup_auto
if /i not "%~2"=="-Python" goto action_setup_usage
if "%~3"=="" goto action_setup_usage
if not "%~4"=="" goto action_setup_usage
"%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%BOOTSTRAP%" -Python "%~3"
exit /b %errorlevel%

:action_setup_auto
"%POWERSHELL%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%BOOTSTRAP%"
exit /b %errorlevel%

:action_setup_usage
>&2 echo Usage: make.bat setup [-Python ^<python-executable^>]
exit /b 2

:action_test
if not exist "%VENV_PYTHON%" (
    >&2 echo The project environment was not found: "%VENV_PYTHON%"
    >&2 echo Run "make.bat setup" first.
    exit /b 1
)
"%VENV_PYTHON%" -m pytest --basetemp=.pytest_tmp
exit /b %errorlevel%

:action_check
if not exist "%VENV_PYTHON%" (
    >&2 echo The project environment was not found: "%VENV_PYTHON%"
    >&2 echo Run "make.bat setup" first.
    exit /b 1
)
"%VENV_PYTHON%" -m ruff format --check upref tests examples scripts docs\conf.py
if errorlevel 1 exit /b %errorlevel%
"%VENV_PYTHON%" -m ruff check upref tests examples scripts docs\conf.py
if errorlevel 1 exit /b %errorlevel%
"%VENV_PYTHON%" -m mypy upref examples
exit /b %errorlevel%

:action_docs
if not exist "%VENV_PYTHON%" (
    >&2 echo The project environment was not found: "%VENV_PYTHON%"
    >&2 echo Run "make.bat setup" first.
    exit /b 1
)
"%VENV_PYTHON%" -m sphinx -E -a -W --keep-going -b html docs docs\_build\html
exit /b %errorlevel%

:action_build
if not exist "%VENV_PYTHON%" (
    >&2 echo The project environment was not found: "%VENV_PYTHON%"
    >&2 echo Run "make.bat setup" first.
    exit /b 1
)
"%VENV_PYTHON%" -m build
if errorlevel 1 exit /b %errorlevel%
"%VENV_PYTHON%" -m twine check dist\*
exit /b %errorlevel%

:action_clean
set "CLEAN_FAILED=0"
for %%D in (
    "%ROOT%build"
    "%ROOT%dist"
    "%ROOT%docs\_build"
    "%ROOT%htmlcov"
    "%ROOT%.pytest_cache"
    "%ROOT%.pytest_tmp"
    "%ROOT%.mypy_cache"
    "%ROOT%.ruff_cache"
    "%ROOT%__pycache__"
) do if exist "%%~D" (
    rmdir /s /q "%%~D"
    if exist "%%~D" set "CLEAN_FAILED=1"
)

for /d %%D in ("%ROOT%*.egg-info") do if exist "%%~fD" (
    rmdir /s /q "%%~fD"
    if exist "%%~fD" set "CLEAN_FAILED=1"
)

for %%R in (upref tests examples scripts docs) do (
    if exist "%ROOT%%%R" (
        for /d /r "%ROOT%%%R" %%D in (__pycache__) do if exist "%%~fD" (
            rmdir /s /q "%%~fD"
            if exist "%%~fD" set "CLEAN_FAILED=1"
        )
    )
)

del /q "%ROOT%.coverage" "%ROOT%.coverage.*" "%ROOT%coverage.xml" "%ROOT%tests\test_result.xml" >nul 2>&1
if "!CLEAN_FAILED!"=="1" (
    >&2 echo Some generated artifacts could not be removed.
    exit /b 1
)
exit /b 0

:action_help
set "HELP_EXIT_CODE=0"

:print_help
echo Usage: make.bat ^<action^>
echo.
echo Actions:
echo   setup [-Python ^<path^>]  Create/update .venv and install the dev environment
echo   test                     Run the test suite
echo   check                    Check formatting, lint, and static typing
echo   docs                     Build the Sphinx documentation
echo   build                    Build source and wheel distributions
echo   clean                    Remove project build and cache artifacts
echo   help                     Show this help
exit /b %HELP_EXIT_CODE%
