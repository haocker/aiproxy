# 高级使用指南

## 目录
1. [SSE 流媒体支持](#sse-流媒体支持)
2. [HTTPS 配置](#https-配置)
3. [多域名转发](#多域名转发)
4. [API 开发指南](#api-开发指南)
5. [性能优化](#性能优化)
6. [常见问题](#常见问题)

## SSE 流媒体支持

### 什么是 SSE

Server-Sent Events (SSE) 是一种用于实时数据推送的技术，常用于：
- 实时通知
- 流媒体传输
- 聊天应用
- 实时日志

### 工作原理

本代理完全透明地处理 SSE 连接：

```
客户端 --HTTP--> 代理 --HTTP--> 服务器
                 (识别 text/event-stream)
       <--SSE-- (转发)   <--SSE--
```

### 测试 SSE

使用 curl 测试 SSE 响应：

```bash
# 测试目标服务器
curl -N https://api.example.com/events

# 通过代理测试（需要配置 hosts）
curl -N http://example.local/events
```

### 在前端使用

```javascript
const eventSource = new EventSource('http://example.local/api/stream');

eventSource.addEventListener('message', (e) => {
  console.log('Data:', JSON.parse(e.data));
});

eventSource.addEventListener('error', () => {
  console.error('Connection error');
});
```

## HTTPS 配置

### 生成自签名证书

```bash
# 生成私钥
openssl genrsa -out key.pem 2048

# 创建 CSR (Certificate Signing Request)
openssl req -new -key key.pem -out csr.pem \
  -subj "/CN=example.local/O=Company/C=US"

# 生成自签名证书
openssl x509 -req -days 365 -in csr.pem \
  -signkey key.pem -out cert.pem

# 验证证书
openssl x509 -in cert.pem -text -noout
```

### 配置 HTTPS

编辑 `config.json`:

```json
{
  "https": {
    "enabled": true,
    "cert_path": "/abs/path/to/cert.pem",
    "key_path": "/abs/path/to/key.pem"
  },
  "port": 8443
}
```

### 浏览器信任

对于自签名证书，浏览器会显示警告。可以：

1. **临时允许** - 在警告页面点击"继续"
2. **添加到信任** - 将证书导入到系统证书库
   - Windows: certmgr.msc
   - macOS: Keychain
   - Linux: /usr/local/share/ca-certificates/

## 多域名转发

### 配置多个服务

```json
{
  "proxy_rules": {
    "api.local": "api.production.com",
    "web.local": "web.production.com",
    "admin.local": "admin.production.com",
    "ws.local": "websocket.production.com",
    "cdn.local": "cdn.production.com"
  }
}
```

### 配置 hosts 文件

**Linux/macOS** (`/etc/hosts`):
```
127.0.0.1 api.local
127.0.0.1 web.local
127.0.0.1 admin.local
127.0.0.1 ws.local
127.0.0.1 cdn.local
```

**Windows** (`C:\Windows\System32\drivers\etc\hosts`):
```
127.0.0.1 api.local
127.0.0.1 web.local
127.0.0.1 admin.local
127.0.0.1 ws.local
127.0.0.1 cdn.local
```

## API 开发指南

### 完整的 API 流程

```python
import requests
import json

BASE_URL = "http://localhost:8080/api"

# 1. 获取当前配置
config = requests.get(f"{BASE_URL}/config").json()
print(json.dumps(config, indent=2))

# 2. 添加新规则
response = requests.post(
    f"{BASE_URL}/rules",
    json={
        "source": "newapp.local",
        "target": "newapp.production.com"
    }
)
print(response.json())

# 3. 获取所有规则
rules = requests.get(f"{BASE_URL}/rules").json()
print(json.dumps(rules, indent=2))

# 4. 测试代理
test_result = requests.post(
    f"{BASE_URL}/test",
    json={"url": "https://api.production.com/health"}
).json()
print(json.dumps(test_result, indent=2))

# 5. 删除规则
delete_response = requests.delete(
    f"{BASE_URL}/rules/oldapp.local"
)
print(delete_response.json())

# 6. 更新全局配置
new_config = config.copy()
new_config['log_level'] = 'DEBUG'
new_config['port'] = 8081

update_response = requests.post(
    f"{BASE_URL}/config",
    json=new_config
)
print(update_response.json())
```

### Python 客户端类

```python
class ProxyAPIClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def get_config(self):
        """获取配置"""
        return requests.get(f"{self.api_url}/config").json()
    
    def add_rule(self, source, target):
        """添加规则"""
        return requests.post(
            f"{self.api_url}/rules",
            json={"source": source, "target": target}
        ).json()
    
    def delete_rule(self, source):
        """删除规则"""
        return requests.delete(
            f"{self.api_url}/rules/{source}"
        ).json()
    
    def test_proxy(self, url):
        """测试代理"""
        return requests.post(
            f"{self.api_url}/test",
            json={"url": url}
        ).json()
    
    def get_rules(self):
        """获取所有规则"""
        return requests.get(f"{self.api_url}/rules").json()

# 使用示例
client = ProxyAPIClient()
client.add_rule("test.local", "test.example.com")
print(client.get_rules())
```

## 性能优化

### 日志级别调优

```json
{
  "log_level": "WARNING"
}
```

- **DEBUG**: 最详细，包含所有请求/响应细节 (开发)
- **INFO**: 标准级别，记录重要信息 (推荐)
- **WARNING**: 仅记录警告和错误 (生产)
- **ERROR**: 仅记录错误 (最小开销)

### 连接优化

代理自动使用：
- 连接池复用
- 自动重试机制
- 超时控制 (30 秒)

### 内存管理

- 流式处理大文件响应
- SSE 连接自动清理
- 定期日志轮转

## 常见问题

### Q: 域名无法解析

A: 确保在 hosts 文件中添加了映射：
```bash
# Linux/macOS
sudo nano /etc/hosts
# 添加：127.0.0.1 example.local

# Windows
notepad C:\Windows\System32\drivers\etc\hosts
# 添加：127.0.0.1 example.local
```

### Q: 获得 HTTPS 证书错误

A: 
1. 检查证书文件是否存在
2. 检查文件路径是否为绝对路径
3. 确保 Python 进程有文件读取权限
4. 检查证书格式（应为 PEM 格式）

### Q: 代理变慢

A:
1. 检查目标服务器响应时间
2. 将日志级别改为 WARNING
3. 检查网络连接
4. 查看 CPU 和内存使用率

### Q: SSE 连接中断

A:
1. 检查网络连接
2. 确认目标服务器支持 SSE
3. 增加服务器超时时间
4. 检查代理日志

### Q: 端口被占用

A:
```bash
# 查看端口占用情况
# Linux/macOS
lsof -i :8080

# Windows
netstat -ano | findstr :8080

# 修改 config.json 中的端口号
```

### Q: 如何在生产环境使用

A: 推荐步骤：
1. 使用 HTTPS 和有效证书
2. 设置日志级别为 WARNING
3. 配置日志文件轮转
4. 使用反向代理 (nginx) 前置
5. 实施访问控制和认证
6. 定期备份配置文件

---

更多帮助请查看 [README.md](README.md)
