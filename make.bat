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
:MAKE_ACTION
CALL :CONFIGURE_DISPLAY
CALL :CLEAR_SCREEN

SET MYPATH=%~dp0
cd %MYPATH%

CALL :PRINT_LINE "    MYPATH=%MYPATH%" 
CALL :LINE_BREAK

IF /I "%1" == "setup" GOTO :action_setup

CALL :PRINT_LINE "   '%1' is not an action. Can not find the right action." 
GOTO :ENDOFFILE

REM -------------------------------------------------------------------------------
:action_setup
CALL :PRINT_LINE "   Setup python packages" 
REM -------------------------------------------------------------------------------
python -V
pip -V
python -m pip install --upgrade pip wheel setuptools
pip install vulture
pip install twine
pip install pytest
pip install -U wxPython
pip install pyyaml
pip install sphinx
goto :ENDOFFILE

:install
echo INSTALL
goto :ENDOFFILE

:tikzpgf
echo TIKZPGF
goto :ENDOFFILE

:clean
echo CLEAN
goto :ENDOFFILE


REM -------------------------------------------------------------------------------
:ENDOFFILE
CALL :PRINT_LINE "   End of the configuration"
CALL :LINE_BREAK
PAUSE
REM -------------------------------------------------------------------------------
