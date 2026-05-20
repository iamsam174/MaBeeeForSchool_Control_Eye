@echo off
rem MaBeeeForSchool Control Eye Build Script
echo ========================================
echo  MaBeeeForSchool Control Eye EXE Build Start
echo ========================================
cd /d %~dp0

python -m PyInstaller MabeeeForSchool_Control_Eye.spec --clean

echo.
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build Failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [SUCCESS] Build Finished! 
echo Please check the "dist\MabeeeForSchool_Control_Eye" folder.
echo You can run "MabeeeForSchool_Control_Eye.exe" inside that folder.
echo To distribute, please ZIP the entire "MabeeeForSchool_Control_Eye" folder.
pause
