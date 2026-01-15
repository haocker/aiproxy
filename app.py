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
from proxy_server import ProxyServer

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
    
    def __init__(self, proxy_server):
        self.proxy_server = proxy_server
        logger.info("AppAPI initialized")
    
    def get_config(self):
        """Get current configuration"""
        return self.proxy_server.config
    
    def update_config(self, config):
        """Update configuration"""
        return self.proxy_server.save_config(config)
    
    def add_rule(self, source, target):
        """Add a proxy rule"""
        if not source or not target:
            logger.warning(f"Invalid rule - source: {source}, target: {target}")
            return {"status": "error", "message": "Missing source or target"}
        
        self.proxy_server.config['proxy_rules'][source] = target
        if self.proxy_server.save_config(self.proxy_server.config):
            logger.info(f"Rule added: {source} -> {target}")
            return {"status": "success", "rule": {source: target}}
        logger.error(f"Failed to save config")
        return {"status": "error", "message": "Failed to save config"}
    
    def delete_rule(self, source):
        """Delete a proxy rule"""
        if source in self.proxy_server.config.get('proxy_rules', {}):
            del self.proxy_server.config['proxy_rules'][source]
            if self.proxy_server.save_config(self.proxy_server.config):
                logger.info(f"Rule deleted: {source}")
                return {"status": "success"}
        logger.warning(f"Rule not found: {source}")
        return {"status": "error", "message": "Rule not found"}
    
    def get_rules(self):
        """Get all proxy rules"""
        return self.proxy_server.config.get('proxy_rules', {})
    
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
    
    # Initialize proxy server
    logger.info("Initializing proxy server...")
    proxy_server = ProxyServer(str(app_dir / 'config.json'))
    logger.info(f"Proxy server initialized on port {proxy_server.config.get('port', 8080)}")
    
    # Create API
    api = AppAPI(proxy_server)
    
    # Start proxy server in a separate thread
    def run_proxy():
        time.sleep(2)  # Wait for webview to initialize
        logger.info("Starting proxy server...")
        proxy_server.run(host='127.0.0.1', port=proxy_server.config.get('port', 8080), debug=False)
    
    proxy_thread = threading.Thread(target=run_proxy, daemon=True)
    proxy_thread.start()
    
    if not WEBVIEW_AVAILABLE:
        logger.info("PyWebView not available, running proxy only")
        proxy_thread.join()
        return
    
    # Create webview
    logger.info("Creating WebView window...")
    window = webview.create_window(
        title='HTTP/HTTPS 代理管理系统',
        url=str(html_file),
        css="""
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }
        """,
        width=1200,
        height=800,
        min_size=(800, 600)
    )
    
    logger.info("Starting WebView...")
    # Start webview
    webview.start(api, window, debug=False)


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

