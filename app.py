"""
HTTP/HTTPS Proxy with PyWebView GUI
Main application entry point
"""
import os
import sys
import threading
import time
import json
import logging
from pathlib import Path
from mitm_proxy import MITMProxyServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    logger.warning("pywebview not available, will run proxy only")


class AppAPI:
    """API for the frontend to communicate with the proxy server"""

    def __init__(self, config_path: str, proxy_config: dict):
        self.config_path = config_path
        self.proxy_config = proxy_config
        logger.info("AppAPI initialized")

    def _load_config(self) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.proxy_config = config
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.proxy_config

    def _save_config(self, config: dict) -> bool:
        """Save configuration to JSON file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.proxy_config = config
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def get_config(self):
        """Get current configuration"""
        return self._load_config()

    def get_https_status(self):
        """Get HTTPS certificate status"""
        ca_cert_path = Path(__file__).parent / '.certs' / 'ca-cert.pem'
        return {
            "enabled": True,
            "ca_cert_exists": ca_cert_path.exists(),
            "ca_cert_path": str(ca_cert_path),
            "mode": "MITM"
        }

    def import_ca_cert(self):
        """Import CA certificate to system trust store"""
        import subprocess
        import os
        import platform
        
        ca_cert_path = Path(__file__).parent / '.certs' / 'ca-cert.pem'
        if not ca_cert_path.exists():
            return {"status": "error", "message": "CA证书文件不存在"}
        
        system = platform.system()
        
        try:
            if system == "Windows":
                # Windows: 使用certutil导入到受信任的根证书颁发机构
                result = subprocess.run(
                    ['certutil', '-addstore', '-f', 'ROOT', str(ca_cert_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return {
                        "status": "success", 
                        "message": "CA证书已成功导入到系统受信任根证书颁发机构"
                    }
                else:
                    return {"status": "error", "message": f"导入失败: {result.stderr}"}
            
            elif system == "Darwin":  # macOS
                # macOS: 导入到系统钥匙串
                result = subprocess.run(
                    ['sudo', 'security', 'add-trusted-cert', '-d', '-r', 'trustRoot', '-k', '/Library/Keychains/System.keychain', str(ca_cert_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return {
                        "status": "success",
                        "message": "CA证书已成功导入到系统钥匙串"
                    }
                else:
                    return {"status": "error", "message": f"导入失败: {result.stderr}"}
            
            elif system == "Linux":
                # Linux: 导入到系统证书目录
                cert_dir = Path('/usr/local/share/ca-certificates')
                if not cert_dir.exists():
                    cert_dir = Path('/usr/share/ca-certificates')
                
                if cert_dir.exists():
                    # 复制证书到系统目录
                    import shutil
                    target_path = cert_dir / 'aiproxy-ca.crt'
                    shutil.copy2(str(ca_cert_path), str(target_path))
                    
                    # 更新证书存储
                    result = subprocess.run(['sudo', 'update-ca-certificates'], capture_output=True, text=True)
                    if result.returncode == 0:
                        return {
                            "status": "success",
                            "message": "CA证书已成功导入到系统证书存储"
                        }
                    else:
                        return {"status": "error", "message": f"更新证书失败: {result.stderr}"}
                else:
                    return {"status": "error", "message": "未找到系统证书目录，请手动导入"}
            
            else:
                return {"status": "error", "message": f"不支持的操作系统: {system}"}
                
        except FileNotFoundError:
            return {"status": "error", "message": "找不到系统证书管理工具，请手动导入"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def update_config(self, config):
        """Update configuration"""
        return self._save_config(config)

    def add_rule(self, source, target):
        """Add a proxy rule"""
        if not source or not target:
            logger.warning(f"Invalid rule - source: {source}, target: {target}")
            return {"status": "error", "message": "Missing source or target"}

        self.proxy_config['proxy_rules'][source] = target
        if self._save_config(self.proxy_config):
            logger.info(f"Rule added: {source} -> {target}")
            return {"status": "success", "rule": {source: target}}
        logger.error(f"Failed to save config")
        return {"status": "error", "message": "Failed to save config"}

    def delete_rule(self, source):
        """Delete a proxy rule"""
        if source in self.proxy_config.get('proxy_rules', {}):
            del self.proxy_config['proxy_rules'][source]
            if self._save_config(self.proxy_config):
                logger.info(f"Rule deleted: {source}")
                return {"status": "success"}
        logger.warning(f"Rule not found: {source}")
        return {"status": "error", "message": "Rule not found"}

    def get_rules(self):
        """Get all proxy rules"""
        return self.proxy_config.get('proxy_rules', {})

    def test_url(self, url):
        """Test a URL"""
        try:
            import requests
            resp = requests.get(url, timeout=10, verify=False)
            logger.info(f"Test request successful: {url} - {resp.status_code}")
            return {
                "status": "success",
                "status_code": resp.status_code,
                "preview": resp.text[:500]
            }
        except Exception as e:
            logger.error(f"Test request failed: {url} - {e}")
            return {"status": "error", "message": str(e)}


def create_app():
    """Create and configure the main application"""
    # Get the directory of the main script
    app_dir = Path(__file__).parent
    static_dir = app_dir / 'static'
    
    # Create static directory if it doesn't exist
    static_dir.mkdir(exist_ok=True)
    
    # Load config
    logger.info("加载配置文件...")
    config_path = str(app_dir / 'config.json')
    proxy_config = MITMProxyServer().load_config()
    
    # Initialize MITM proxy server (this will generate CA cert if needed)
    logger.info("初始化MITM代理服务器...")
    proxy_server = MITMProxyServer(
        host='127.0.0.1',
        port=proxy_config.get('port', 8080)
    )
    
    logger.info(f"代理服务器初始化完成，端口 {proxy_server.port}")
    ca_cert_path = app_dir / '.certs' / 'ca-cert.pem'
    logger.info(f"CA证书路径: {ca_cert_path}")
    logger.info(f"CA证书{'已' if ca_cert_path.exists() else '未'}生成")
    
    # Create HTML file if it doesn't exist
    html_file = static_dir / 'index.html'
    if not html_file.exists():
        logger.warning("index.html not found in static directory")
        # Create a simple fallback HTML
        html_file.write_text("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>代理管理系统</title>
            <style>
                body { font-family: Arial; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
                h1 { color: #667eea; }
                button { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
                input { padding: 8px; border: 1px solid #ddd; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>HTTP/HTTPS 代理管理系统</h1>
                <p>代理管理系统已启动，正在加载界面...</p>
            </div>
        </body>
        </html>
        """)
    
    # Create API
    api = AppAPI(config_path, proxy_config)
    
    # Start proxy server in a separate thread
    def run_proxy():
        time.sleep(2)  # Wait for webview to initialize
        logger.info("Starting proxy server...")
        proxy_server.run()
    
    proxy_thread = threading.Thread(target=run_proxy, daemon=True)
    proxy_thread.start()
    
    if not WEBVIEW_AVAILABLE:
        logger.info("PyWebView not available, running proxy only")
        proxy_thread.join()
        return
    
    # Create webview
    logger.info("Creating WebView window...")
    webview.create_window(
        title='HTTP/HTTPS MITM代理管理系统',
        url=str(html_file),
        width=1200,
        height=800,
        min_size=(800, 600),
        js_api=api
    )
    
    logger.info("Starting WebView...")
    # Start webview
    webview.start(debug=False)


if __name__ == '__main__':
    try:
        logger.info("=" * 60)
        logger.info("HTTP/HTTPS 代理管理系统启动")
        logger.info("=" * 60)
        create_app()
    except KeyboardInterrupt:
        logger.info("\n应用已关闭")
        sys.exit(0)
    except Exception as e:
        logger.error(f"错误: {e}", exc_info=True)
        sys.exit(1)

