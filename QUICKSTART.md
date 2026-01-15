# 快速开始指南

## 5 分钟快速上手

### 1. 安装依赖（首次运行）

```bash
# Linux/macOS
chmod +x run.sh
./run.sh

# Windows
run.bat
```

脚本会自动：
- ✓ 创建 Python 虚拟环境
- ✓ 安装所有必要的依赖
- ✓ 启动应用

### 2. 应用启动

应用启动后会：
- 🔗 自动打开 PyWebView 窗口
- 🌐 显示管理界面
- 🚀 在后台启动代理服务器

### 3. 基本配置

#### 第一步：添加代理规则

在"配置规则"卡片中：

1. **源域名** (A域名): `example.local`
2. **目标域名** (B域名): `api.example.com`
3. 点击 **➕ 添加规则**

#### 第二步：配置 hosts 文件

**Linux/macOS**:
```bash
sudo nano /etc/hosts
# 添加这一行：
127.0.0.1 example.local
```

**Windows** (以管理员身份运行):
```
notepad C:\Windows\System32\drivers\etc\hosts
# 添加这一行：
127.0.0.1 example.local
```

#### 第三步：测试代理

在"测试工具"卡片中：
1. 输入测试 URL: `https://api.example.com/health`
2. 点击 **🚀 测试请求**
3. 查看响应结果

### 4. 常用命令

```bash
# 仅启动代理服务器（无 GUI）
./run.sh proxy-only

# 直接运行 Python 脚本
python app.py          # 使用 GUI
python proxy_server.py # 仅服务器

# 停止应用
Ctrl + C
```

## 使用场景

### 场景 1：本地开发

```json
{
  "proxy_rules": {
    "api.local": "api.staging.com",
    "web.local": "web.staging.com"
  }
}
```

配置后：
- `http://api.local/users` → `https://api.staging.com/users`
- `http://web.local/` → `https://web.staging.com/`

### 场景 2：多环境测试

```json
{
  "proxy_rules": {
    "dev.local": "dev.example.com",
    "test.local": "test.example.com",
    "stage.local": "stage.example.com",
    "prod.local": "prod.example.com"
  }
}
```

### 场景 3：API 版本控制

```json
{
  "proxy_rules": {
    "apiv1.local": "api.example.com/v1",
    "apiv2.local": "api.example.com/v2",
    "apiv3.local": "api.example.com/v3"
  }
}
```

## 配置文件详解

`config.json` 示例：

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

| 字段 | 说明 | 示例 |
|------|------|------|
| proxy_rules | 转发规则 | {"local": "remote"} |
| https.enabled | 启用 HTTPS | true/false |
| https.cert_path | 证书路径 | "./cert.pem" |
| https.key_path | 密钥路径 | "./key.pem" |
| port | 监听端口 | 8080 |
| log_level | 日志级别 | INFO/DEBUG/WARNING |

## Web 界面功能

### 📝 配置规则

- ➕ **添加规则** - 输入源域名和目标域名
- 🗑️ **删除规则** - 移除不需要的规则
- 📋 **规则列表** - 查看当前所有规则

### ⚙️ 系统设置

- 🔌 **监听端口** - 代理服务器端口
- 📊 **日志级别** - 调整日志详细程度
- 🔐 **HTTPS 设置** - 配置 SSL/TLS 证书

### 🧪 测试工具

- 🔗 **输入 URL** - 输入要测试的网址
- 🚀 **发送请求** - 测试代理连接
- 📊 **查看结果** - 显示响应状态和内容

## 常见问题速查

| 问题 | 解决方案 |
|------|--------|
| 端口被占用 | 修改 config.json 中的 port |
| 域名无法解析 | 检查 /etc/hosts 配置 |
| HTTPS 错误 | 检查证书路径和权限 |
| 慢速响应 | 降低日志级别为 WARNING |
| SSE 不工作 | 确认目标服务器支持 SSE |

## 下一步

- 📚 查看 [README.md](README.md) 了解更多功能
- 🔧 查看 [ADVANCED.md](ADVANCED.md) 学习高级用法
- 🐍 查看 [config_examples.py](config_examples.py) 了解配置示例

## 获取帮助

```bash
# 查看日志输出
# 启动应用时会在控制台显示日志

# 调整日志级别
# 在 config.json 中修改 log_level 为 DEBUG

# 检查服务状态
curl http://localhost:8080/api/config
```

---

祝您使用愉快！如有问题，欢迎反馈。
