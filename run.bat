@echo off
REM HTTP/HTTPS Proxy Server - Run Script for Windows

echo ==================================================
echo   HTTP/HTTPS 代理管理系统
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未找到，请先安装 Python
    exit /b 1
)

echo ✓ Python 版本：
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
    echo ✓ 虚拟环境创建成功
)

REM Activate virtual environment
echo 🔄 激活虚拟环境...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 安装依赖...
pip install -r requirements.txt -q

echo.
echo ==================================================
echo   启动参数：
echo   - Web UI: http://localhost:8080
echo   - 支持 SSE (Server-Sent Events)
echo   - 支持 HTTPS
echo   - 可视化配置界面
echo ==================================================
echo.

REM Run the application
if "%1"=="proxy-only" (
    echo 🚀 启动代理服务器 (仅服务器，无GUI)...
    python proxy_server.py
) else (
    echo 🚀 启动应用程序 (使用 PyWebView GUI)...
    python app.py
)
