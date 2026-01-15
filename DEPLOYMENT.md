# 部署和部署指南

## 项目概述

```
HTTP/HTTPS 代理管理系统
├─ 核心功能：HTTP/HTTPS 代理转发
├─ 特色功能：SSE 支持、可视化配置
├─ 前端技术：PyWebView + HTML5 + CSS3
├─ 后端技术：Flask + Python
└─ 配置方式：JSON 文件 + Web 界面
```

## 文件说明

| 文件 | 说明 | 大小 |
|------|------|------|
| [proxy_server.py](proxy_server.py) | 核心代理服务器 (Flask) | 9.5 KB |
| [app.py](app.py) | PyWebView 应用入口 | 5.9 KB |
| [static/index.html](static/index.html) | Web 管理界面 | 22 KB |
| [config.json](config.json) | 配置文件 | 217 B |
| [requirements.txt](requirements.txt) | 依赖列表 | 80 B |
| [run.sh](run.sh) | Linux/macOS 启动脚本 | 1.3 KB |
| [run.bat](run.bat) | Windows 启动脚本 | 1.3 KB |
| [config_examples.py](config_examples.py) | 配置示例 | 3.3 KB |
| [demo.py](demo.py) | 功能演示脚本 | 8.8 KB |
| [README.md](README.md) | 项目说明 | 5.0 KB |
| [QUICKSTART.md](QUICKSTART.md) | 快速开始 | 3.9 KB |
| [ADVANCED.md](ADVANCED.md) | 高级功能 | 6.4 KB |

**总计：约 67 KB** (非常轻量级)

## 系统要求

### 最低要求
- Python 3.8+
- 200 MB 可用磁盘空间
- 256 MB RAM

### 推荐配置
- Python 3.10+
- 1 GB+ 可用磁盘空间
- 512 MB+ RAM

### 操作系统支持
- ✅ Linux (Ubuntu, CentOS, Debian 等)
- ✅ macOS (10.13+)
- ✅ Windows (7+)

## 安装步骤

### 1. 前置条件检查

```bash
# 检查 Python 版本
python3 --version  # 应该是 3.8 或更高

# 检查 pip
python3 -m pip --version
```

### 2. 克隆或下载项目

```bash
git clone https://github.com/haocker/aiproxy.git
cd aiproxy
```

### 3. 创建虚拟环境（可选但推荐）

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 首次运行

```bash
# Linux/macOS
chmod +x run.sh
./run.sh

# Windows
run.bat

# 或直接运行
python app.py
```

## 依赖包说明

```
flask==3.0.0              # Web 框架
flask-cors==4.0.0         # 跨域资源共享
requests==2.31.0          # HTTP 客户端库
pywebview==5.0.0          # GUI 框架
urllib3==2.1.0            # HTTP 客户端 (requests 依赖)
```

**总计大小：约 150 MB** (首次安装)

## 运行方式

### 方式 1：GUI 模式（推荐）

```bash
python app.py
# 或
./run.sh
# 或
run.bat
```

启动后：
- ✓ 自动打开 PyWebView 窗口
- ✓ 显示管理界面
- ✓ 后台运行代理服务器

### 方式 2：服务器模式

```bash
python proxy_server.py
# 或
./run.sh proxy-only
# 或
run.bat proxy-only
```

启动后：
- ✓ 运行 Flask 开发服务器
- ✓ 可通过浏览器访问 http://localhost:8080
- ✓ 无 GUI 界面

### 方式 3：生产部署

使用 gunicorn 或 uWSGI：

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:8080 "proxy_server:ProxyServer('config.json').app"
```

## 配置管理

### 配置文件位置
- 默认：`config.json` (与脚本同目录)

### 配置更新方式

**方式 1：编辑配置文件**
```bash
nano config.json  # 编辑并保存
# 应用会自动重新加载
```

**方式 2：Web 界面**
- 打开 PyWebView 窗口
- 在"系统设置"卡片修改配置
- 点击"保存设置"

**方式 3：API 接口**
```bash
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## 故障排除

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|--------|
| `ModuleNotFoundError: No module named 'flask'` | 缺少依赖 | `pip install -r requirements.txt` |
| `Address already in use` | 端口被占用 | 修改 config.json 中的 port |
| `Permission denied` | 权限不足 | `chmod +x run.sh` (Linux/macOS) |
| `Certificate error` | HTTPS 证书问题 | 检查证书路径和权限 |
| `Domain not found` | 缺少 hosts 配置 | 编辑 /etc/hosts (Linux/macOS) |

### 调试方法

**启用调试日志**
```bash
# 修改 config.json
{
  "log_level": "DEBUG"
}
```

**查看实时日志**
```bash
# 控制台会显示所有日志
# 查找关键词：ERROR, WARNING, INFO
```

**测试连接**
```bash
curl http://localhost:8080/api/config
```

## 性能优化建议

### 生产环境设置

1. **关闭调试日志**
   ```json
   {
     "log_level": "WARNING"
   }
   ```

2. **使用生产级服务器**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8080 app:create_app()
   ```

3. **启用进程管理**
   ```bash
   pip install supervisord
   # 配置 supervisord.conf
   ```

4. **使用反向代理**
   ```nginx
   # nginx.conf
   upstream proxy {
       server 127.0.0.1:8080;
   }
   
   server {
       listen 80;
       location / {
           proxy_pass http://proxy;
       }
   }
   ```

## 安全建议

### 基本安全措施

1. **限制访问**
   ```bash
   # 仅本机访问
   bind_address: 127.0.0.1
   ```

2. **启用 HTTPS**
   - 生成或获取有效证书
   - 在 config.json 中启用 HTTPS

3. **访问控制**
   - 在反向代理层实施身份验证
   - 使用防火墙限制端口访问

4. **日志监控**
   - 定期检查日志
   - 监控异常流量

## 监控和维护

### 系统监控

```bash
# 监控端口
lsof -i :8080

# 监控进程
ps aux | grep python

# 监控资源使用
top | grep python
```

### 定期维护

1. **定期备份配置**
   ```bash
   cp config.json config.json.backup
   ```

2. **更新依赖**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **清理日志**
   - 实施日志轮转策略
   - 定期归档旧日志

## 常见部署场景

### 场景 1：本地开发

```bash
# 快速启动
./run.sh

# 配置本地环境
echo "127.0.0.1 example.local" >> /etc/hosts

# 开发测试
curl http://example.local:8080
```

### 场景 2：局域网部署

```bash
# 配置外网访问
# proxy_server.py 中：
proxy_server.run(host='0.0.0.0', port=8080)

# 防火墙规则（Linux）
sudo ufw allow 8080/tcp

# 其他机器访问
curl http://server-ip:8080/api/config
```

### 场景 3：Docker 容器

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8080
CMD ["python", "proxy_server.py"]
```

```bash
# 构建
docker build -t aiproxy .

# 运行
docker run -p 8080:8080 -v $(pwd)/config.json:/app/config.json aiproxy
```

### 场景 4：K8s 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiproxy
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aiproxy
  template:
    metadata:
      labels:
        app: aiproxy
    spec:
      containers:
      - name: aiproxy
        image: aiproxy:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: config
          mountPath: /app/config.json
          subPath: config.json
      volumes:
      - name: config
        configMap:
          name: aiproxy-config
```

## 许可和贡献

- **许可**：MIT License
- **作者**：Haocker
- **贡献**：欢迎 Pull Requests

## 获取帮助

- 📖 查看文档：README.md, QUICKSTART.md, ADVANCED.md
- 🐛 报告 Bug：GitHub Issues
- 💬 讨论功能：GitHub Discussions
- 📧 邮件联系：通过 GitHub Profile

---

**最后更新**：2026-01-15
**项目状态**：✅ 生产就绪
