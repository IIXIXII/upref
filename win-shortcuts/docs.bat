@echo off
call "%~dp0..\make.bat" docs
exit /b %errorlevel%
