@echo off
:: Set UTF-8 encoding for Windows Command Prompt to support Vietnamese characters
chcp 65001 > nul

echo ========================================================================
echo     🛡️  ĐANG KHỞI CHẠY HỆ THỐNG PHÁT HIỆN XÂM NHẬP MẠNG (IDS) AI  🛡️
echo                    -- BÀI TẬP LỚN NHÓM 10 --
echo ========================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Không tìm thấy Python trong hệ thống!
    echo Vui lòng cài đặt Python (phiên bản khuyên dùng: 3.9 - 3.11) và thêm vào PATH.
    pause
    exit /b 1
)

:: 2. Check and create Python virtual environment (venv)
if not exist "venv" (
    echo [*] Đang khởi tạo môi trường ảo Python (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Tạo môi trường ảo thất bại!
        pause
        exit /b 1
    )
    echo [✓] Đã tạo môi trường ảo thành công.
    echo.
)

:: 3. Activate venv
echo [*] Đang kích hoạt môi trường ảo...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Kích hoạt môi trường ảo thất bại!
    pause
    exit /b 1
)
echo [✓] Đã kích hoạt môi trường ảo.
echo.

:: 4. Install / Update dependencies
echo [*] Đang kiểm tra và cài đặt các thư viện cần thiết (requirements.txt)...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Cài đặt thư viện thất bại!
    pause
    exit /b 1
)
echo [✓] Cài đặt thư viện hoàn tất.
echo.

:: 5. Launch the main script
echo [*] Khởi động giao diện điều khiển ứng dụng...
timeout /t 1 > nul
cls
python run_project.py

:: 6. Deactivate when finished
call venv\Scripts\deactivate
