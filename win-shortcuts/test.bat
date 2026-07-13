@echo off
call "%~dp0..\make.bat" test
exit /b %errorlevel%
