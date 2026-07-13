@echo off
call "%~dp0..\make.bat" check
exit /b %errorlevel%
