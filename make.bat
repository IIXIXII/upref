@ECHO off
REM ###############################################################################
REM # 
REM # Copyright (c) 2018 Florent TOURNOIS
REM # 
REM # Permission is hereby granted, free of charge, to any person obtaining a copy
REM # of this software and associated documentation files (the "Software"), to deal
REM # in the Software without restriction, including without limitation the rights
REM # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
REM # copies of the Software, and to permit persons to whom the Software is
REM # furnished to do so, subject to the following conditions:
REM # 
REM # The above copyright notice and this permission notice shall be included in 
REM # all copies or substantial portions of the Software.
REM # 
REM # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
REM # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
REM # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
REM # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
REM # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
REM # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
REM # SOFTWARE.
REM # 
REM ###############################################################################
GOTO MAKE_ACTION
REM -------------------------------------------------------------------------------
:PRINT_LINE <textVar>
(
    SET "LINE_HERE=%~1"
    SETLOCAL EnableDelayedExpansion
    @ECHO !LINE_HERE!
    ENDLOCAL
    exit /b
)
REM -------------------------------------------------------------------------------
:CONFIGURE_DISPLAY
(
    CHCP 65001
    MODE 100,40
    exit /b
)
REM -------------------------------------------------------------------------------
:CLEAR_SCREEN
(
	CLS
    CALL :PRINT_LINE "╔══════════════════════════════════════════════════════════════════════════════════════════════════╗"
    CALL :PRINT_LINE "║                                _    _   _____           __                                       ║"
    CALL :PRINT_LINE "║                               | |  | | |  __ \         / _|                                      ║"
    CALL :PRINT_LINE "║                               | |  | | | |__) | __ ___| |_                                       ║"
    CALL :PRINT_LINE "║                               | |  | | |  ___/ '__/ _ \  _|                                      ║"
    CALL :PRINT_LINE "║                               | |__| | | |   | | |  __/ |                                        ║"
    CALL :PRINT_LINE "║                                \____/  |_|   |_|  \___|_|                                        ║"
    CALL :PRINT_LINE "║                                                                                                  ║"
    CALL :PRINT_LINE "╚══════════════════════════════════════════════════════════════════════════════════════════════════╝"
    exit /b
)
REM -------------------------------------------------------------------------------
:LINE_BREAK
(
	CALL :PRINT_LINE "├──────────────────────────────────────────────────────────────────────────────────────────────────┤"
    exit /b
)
REM -------------------------------------------------------------------------------
:UPDATE_PIP
(
    python -V
    pip -V
    python -m pip install --upgrade pip wheel setuptools
    exit /b
)
:MAKE_ACTION
CALL :CONFIGURE_DISPLAY
CALL :CLEAR_SCREEN

SET MYPATH=%~dp0
cd %MYPATH%

CALL :PRINT_LINE "    MYPATH=%MYPATH%" 
CALL :LINE_BREAK

IF /I "%1" == "requirements"  GOTO :action_requirements
IF /I "%1" == "requirements-dev"  GOTO :action_requirements_dev
IF /I "%1" == "install-editable"  GOTO :action_install_editable
IF /I "%1" == "test"  GOTO :action_test
IF /I "%1" == "doxygen"  GOTO :action_doxygen

CALL :PRINT_LINE "   '%1' is not an action. Can not find the right action." 
GOTO :ENDOFFILE

REM -------------------------------------------------------------------------------
:action_requirements
CALL :PRINT_LINE "   Requirements python packages for running the lib" 
REM -------------------------------------------------------------------------------
CALL :UPDATE_PIP
pip install -r requirements.txt
goto :ENDOFFILE

REM -------------------------------------------------------------------------------
:action_requirements_dev
CALL :PRINT_LINE "   Requirements python packages for devs" 
REM -------------------------------------------------------------------------------
CALL :UPDATE_PIP
pip install -r requirements-dev.txt
goto :ENDOFFILE

REM -------------------------------------------------------------------------------
:action_install_editable
CALL :PRINT_LINE "   Install editable version" 
REM -------------------------------------------------------------------------------
CALL :UPDATE_PIP
pip install -e .
goto :ENDOFFILE

REM -------------------------------------------------------------------------------
:action_test
CALL :PRINT_LINE "   Launch test" 
REM -------------------------------------------------------------------------------
pytest -v
goto :ENDOFFILE

REM -------------------------------------------------------------------------------
:action_doxygen
CALL :PRINT_LINE "   Doxygen" 
REM -------------------------------------------------------------------------------
cd docs
SET DOXYGEN_PATH=C:\\Program Files\\doxygen\\bin
SET DOXYGEN_EXE=doxygen.exe
SET DOXYGEN_CMD=%DOXYGEN_PATH%\\%DOXYGEN_EXE%
SET DOC_FOLDER=%~dp0\\docs

SET CONFIG_FILE="%DOC_FOLDER%\\config_doc.dox"

IF EXIST "%DOXYGEN_CMD%" (
    ECHO "Found doxygen %DOXYGEN_CMD%"
) ELSE (
    ECHO "%DOXYGEN_CMD%"
    ECHO "Doxygen not found"
    pause
    GOTO:END
)

IF EXIST "%CONFIG_FILE%" (
    ECHO "Found config file %CONFIG_FILE%"
) ELSE (
    ECHO "%CONFIG_FILE%"
    ECHO "Config file not found"
    pause
    GOTO:END
)

CALL :PRINT_LINE "Start doxygen generation"
"%DOXYGEN_CMD%"  "%CONFIG_FILE%"

goto :ENDOFFILE

REM -------------------------------------------------------------------------------
:ENDOFFILE
CALL :PRINT_LINE "   End of the configuration"
CALL :LINE_BREAK
PAUSE
REM -------------------------------------------------------------------------------
