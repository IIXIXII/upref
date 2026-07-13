@echo off
call "%~dp0..\make.bat" build
exit /b %errorlevel%
