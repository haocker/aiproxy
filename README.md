# HTTP/HTTPS 代理管理系统

一个功能完整的 HTTP/HTTPS 代理服务器，支持 SSE、可视化配置界面、域名转发等功能。

## 功能特性

- ✨ **HTTP/HTTPS 代理** - 支持 HTTP 和 HTTPS 请求代理
- 📡 **SSE 支持** - 完整的 Server-Sent Events 流媒体支持
- 🎨 **可视化界面** - 使用 PyWebView 和 HTML5 创建的现代化界面
- 🔧 **域名转发** - 灵活的域名转发规则配置
- 📝 **JSON 配置** - 方便的 JSON 格式配置文件
- 🚀 **零配置启动** - 开箱即用，一键启动
- 🔒 **HTTPS 支持** - 完整的 HTTPS 证书支持

## 快速开始

```bash
# Linux/macOS
chmod +x run.sh
./run.sh

# Windows
run.bat
```

应用启动后会自动打开 PyWebView 窗口显示管理界面。

## 安装

### 前置要求

- Python 3.8+
- pip (Python 包管理器)

### 安装步骤

1. **克隆或下载项目**
   ```bash
   git clone https://github.com/haocker/aiproxy.git
   cd aiproxy
   ```

2. **安装依赖**
   ```bash
   # Linux/macOS
   chmod +x run.sh
   ./run.sh

   # Windows
   run.bat

   # 或手动安装
   pip install -r requirements.txt
   ```

## 使用

### 启动应用

**方式 1：使用 GUI 界面（推荐）**
```bash
# Linux/macOS
./run.sh

# Windows
run.bat

# 或直接运行
python app.py
```

**方式 2：仅启动代理服务器**
```bash
# Linux/macOS
./run.sh proxy-only

# Windows
run.bat proxy-only

# 或直接运行
python proxy_server.py
```

### 配置说明

配置文件：`config.json`

```json
{
  "proxy_rules": {
    "example.local": "example.com",
    "api.local": "api.example.com"
  },
  "https": {
    "enabled": false,
    "cert_path": "",
    "key_path": ""
  },
  "port": 8080,
  "log_level": "INFO"
}
```

**配置项说明：**

- `proxy_rules` - 代理转发规则（键：源域名，值：目标域名）
- `https.enabled` - 是否启用 HTTPS
- `https.cert_path` - HTTPS 证书文件路径
- `https.key_path` - HTTPS 密钥文件路径
- `port` - 代理服务器监听端口
- `log_level` - 日志级别

### 使用界面

启动应用后，会自动打开浏览器窗口显示管理界面：

1. **配置规则** - 添加、查看、删除转发规则
2. **系统设置** - 配置端口、日志级别、HTTPS 等
3. **测试工具** - 测试代理是否正常工作

## 工作原理

### 流程图

```
客户端 → A域名请求 → 代理服务器 → 检查规则 → B域名 → 返回响应
```

### 核心组件

1. **proxy_server.py** - Flask 代理服务器
   - 处理 HTTP/HTTPS 请求
   - 管理转发规则
   - 支持 SSE 流式响应

2. **app.py** - PyWebView 主应用
   - 集成 Flask 服务器
   - 提供 GUI 界面
   - 提供 API 接口

3. **static/index.html** - 前端界面
   - 响应式设计
   - 实时配置管理
   - 请求测试工具

## API 接口

### 获取配置
```
GET /api/config
```

### 更新配置
```
POST /api/config
Content-Type: application/json

{
  "proxy_rules": {...},
  "https": {...},
  "port": 8080,
  "log_level": "INFO"
}
```

### 获取规则
```
GET /api/rules
```

### 添加规则
```
POST /api/rules
Content-Type: application/json

{
  "source": "example.local",
  "target": "example.com"
}
```

### 删除规则
```
DELETE /api/rules/{source}
```

### 测试代理
```
POST /api/test
Content-Type: application/json

{
  "url": "https://api.example.com"
}
```

## HTTPS 配置

### 生成自签名证书

```bash
# 生成私钥
openssl genrsa -out key.pem 2048

# 生成证书
openssl req -new -x509 -key key.pem -out cert.pem -days 365
```

### 在配置文件中启用 HTTPS

编辑 `config.json`：

```json
{
  "https": {
    "enabled": true,
    "cert_path": "/path/to/cert.pem",
    "key_path": "/path/to/key.pem"
  }
}
```

## 设置 hosts 文件

为了测试代理，需要在 hosts 文件中配置源域名：

**Linux/macOS** (`/etc/hosts`)：
```
127.0.0.1 example.local
127.0.0.1 api.local
```

**Windows** (`C:\Windows\System32\drivers\etc\hosts`)：
```
127.0.0.1 example.local
127.0.0.1 api.local
```

## 项目结构

```
aiproxy/
├── proxy_server.py          # 代理服务器核心
├── app.py                   # PyWebView 应用入口
├── config.json              # 配置文件
├── requirements.txt         # 依赖列表
├── run.sh                   # Linux/macOS 启动脚本
├── run.bat                  # Windows 启动脚本
├── static/
│   └── index.html          # Web 管理界面
└── README.md               # 本文档
```

## 故障排除

### 端口已被占用

修改 `config.json` 中的 `port` 字段为其他端口。

### HTTPS 证书错误

确保证书文件路径正确，并且文件存在。

### SSE 不工作

确保代理目标服务器正确响应 `text/event-stream` Content-Type。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**注意：** 这是一个功能演示项目，用于学习和开发目的。在生产环境中使用前，请进行充分的测试和安全审计。
