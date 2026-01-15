#!/bin/bash

# HTTP/HTTPS Proxy Server - Run Script

echo "=================================================="
echo "  HTTP/HTTPS 代理管理系统"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未找到，请先安装 Python 3"
    exit 1
fi

echo "✓ Python 版本: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建成功"
fi

# Activate virtual environment
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# Install dependencies
echo "📥 安装依赖..."
pip install -r requirements.txt -q

echo ""
echo "=================================================="
echo "  启动参数："
echo "  - Web UI: http://localhost:8080"
echo "  - 支持 SSE (Server-Sent Events)"
echo "  - 支持 HTTPS"
echo "  - 可视化配置界面"
echo "=================================================="
echo ""

# Run the application
if [ "$1" == "proxy-only" ]; then
    echo "🚀 启动代理服务器 (仅服务器，无GUI)..."
    python3 proxy_server.py
else
    echo "🚀 启动应用程序 (使用 PyWebView GUI)..."
    python3 app.py
fi
