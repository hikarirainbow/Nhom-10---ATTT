@echo off
:: Set UTF-8 encoding for Windows Command Prompt
chcp 65001 > nul

echo ========================================================================
echo      HE THONG PHAT HIEN XAM NHAP MANG (IDS) AI
echo               -- BAI TAP LON NHOM 10 --
echo ========================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Khong tim thay Python trong he thong!
    echo Vui long cai dat Python phien ban tu 3.9 den 3.11 va them vao PATH.
    pause
    exit /b 1
)

:: 2. Check and create Python virtual environment (venv)
if not exist "venv" (
    echo [*] Dang khoi tao moi truong ao Python venv...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Tao moi truong ao that bai!
        pause
        exit /b 1
    )
    echo [+] Da tao moi truong ao thanh cong.
    echo.
)

:: 3. Activate venv
echo [*] Dang kich hoat moi truong ao...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Kich hoat moi truong ao that bai!
    pause
    exit /b 1
)
echo [+] Da kich hoat moi truong ao.
echo.

:: 4. Install / Update dependencies
echo [*] Dang kiem tra va cai dat cac thu vien can thiet...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Cai dat thu vien that bai!
    pause
    exit /b 1
)
echo [+] Cai dat thu vien hoan tat.
echo.

:: 5. Launch the main script
echo [*] Khoi dong giao dien dieu khien ung dung...
timeout /t 1 > nul
cls
python run_project.py

:: 6. Deactivate when finished
call venv\Scripts\deactivate
