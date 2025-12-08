@echo off
REM MCP Studio Development Setup for Windows
echo 🚀 Setting up MCP Studio development environment...

cd /d "D:\Dev\repos\mcp-studio"
echo 📁 Working in: %CD%

REM Check if venv exists
if exist "venv" (
    echo 📦 Virtual environment already exists
) else (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install packages
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

echo 📚 Installing core dependencies...
pip install fastapi uvicorn pydantic python-dotenv structlog aiofiles watchdog python-multipart jinja2 aiohttp httpx

echo 🛠️ Installing FastMCP...
pip install fastmcp

echo 🧪 Installing development tools...
pip install pytest pytest-asyncio black isort

echo ⚙️ Creating .env file...
if not exist ".env" (
    echo DEBUG=true > .env
    echo LOG_LEVEL=INFO >> .env
    echo HOST=127.0.0.1 >> .env
    echo PORT=8000 >> .env
    echo ✅ .env file created
) else (
    echo ✅ .env file already exists
)

echo.
echo 🧪 Testing installation...
python -c "import fastapi, structlog, aiohttp, httpx; print('✅ All imports successful!')"
if errorlevel 1 (
    echo ❌ Installation test failed
    pause
    exit /b 1
)

echo.
echo ======================================================
echo 🎉 MCP Studio development environment ready!
echo ======================================================
echo 📁 Project: %CD%
echo 🐍 Python: %CD%\venv\Scripts\python.exe
echo.
echo 🚀 To run the development server:
echo    venv\Scripts\activate
echo    python -m uvicorn src.mcp_studio.main:app --reload --port 8000
echo.
echo 🌐 Then visit: http://localhost:8000
echo.
pause
