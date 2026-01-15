"""
HTTP/HTTPS Proxy Server with SSE Support
"""
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Tuple
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import ssl
from cert_manager import CertManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyServer:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
        self.session = self._create_session()
        
    def load_config(self) -> dict:
        """Load configuration from JSON file"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._default_config()
    
    def save_config(self, config: dict) -> bool:
        """Save configuration to JSON file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def _default_config(self) -> dict:
        return {
            "proxy_rules": {},
            "https": {
                "enabled": True,
                "cert_path": "",
                "key_path": "",
                "auto_generate": True
            },
            "port": 8080,
            "log_level": "INFO"
        }
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(500, 502, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def get_target_domain(self, source_domain: str) -> str:
        """Get target domain for source domain"""
        rules = self.config.get('proxy_rules', {})
        return rules.get(source_domain, None)
    
    def proxy_request(self, target_url: str) -> Tuple[Response, int]:
        """Proxy the request to target URL"""
        try:
            # Get request details
            headers = dict(request.headers)
            headers.pop('Host', None)
            
            method = request.method
            params = request.args
            data = request.get_data()
            
            # Make the request
            if method in ['GET', 'DELETE']:
                resp = self.session.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    params=params,
                    timeout=30,
                    allow_redirects=True,
                    verify=False
                )
            else:
                resp = self.session.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=30,
                    allow_redirects=True,
                    verify=False
                )
            
            # Handle SSE responses
            if 'text/event-stream' in resp.headers.get('Content-Type', ''):
                return self._handle_sse(resp), 200
            
            # Build response
            response_headers = {
                k: v for k, v in resp.headers.items()
                if k.lower() not in ['content-encoding', 'transfer-encoding']
            }
            response_headers['Access-Control-Allow-Origin'] = '*'
            
            return Response(
                resp.content,
                status=resp.status_code,
                headers=response_headers
            ), resp.status_code
            
        except requests.exceptions.Timeout:
            return jsonify({"error": "Request timeout"}), 504
        except requests.exceptions.RequestException as e:
            logger.error(f"Proxy request error: {e}")
            return jsonify({"error": "Proxy error", "details": str(e)}), 502
    
    def _handle_sse(self, resp: requests.Response) -> Response:
        """Handle Server-Sent Events streaming"""
        def generate():
            try:
                for chunk in resp.iter_lines():
                    if chunk:
                        yield chunk.decode('utf-8') + '\n'
            except Exception as e:
                logger.error(f"SSE streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            return jsonify(self.config)
        
        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            new_config = request.get_json()
            if self.save_config(new_config):
                return jsonify({"status": "success", "config": self.config})
            return jsonify({"status": "error"}), 400
        
        @self.app.route('/api/rules', methods=['GET'])
        def get_rules():
            return jsonify(self.config.get('proxy_rules', {}))
        
        @self.app.route('/api/rules', methods=['POST'])
        def add_rule():
            data = request.get_json()
            source = data.get('source')
            target = data.get('target')
            
            if not source or not target:
                return jsonify({"error": "Missing source or target"}), 400
            
            self.config['proxy_rules'][source] = target
            if self.save_config(self.config):
                return jsonify({"status": "success", "rule": {source: target}})
            return jsonify({"status": "error"}), 400
        
        @self.app.route('/api/rules/<source>', methods=['DELETE'])
        def delete_rule(source):
            if source in self.config.get('proxy_rules', {}):
                del self.config['proxy_rules'][source]
                if self.save_config(self.config):
                    return jsonify({"status": "success"})
            return jsonify({"error": "Rule not found"}), 404
        
        @self.app.route('/api/test', methods=['POST'])
        def test_proxy():
            """Test proxy with a request"""
            data = request.get_json()
            test_url = data.get('url')
            
            if not test_url:
                return jsonify({"error": "Missing URL"}), 400
            
            try:
                resp = self.session.get(test_url, timeout=10, verify=False)
                return jsonify({
                    "status": "success",
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "preview": resp.text[:500]
                })
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 400
        
        @self.app.route('/<path:url_path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
        def proxy(url_path):
            """Main proxy endpoint"""
            host = request.host.split(':')[0]
            target_domain = self.get_target_domain(host)
            
            if not target_domain:
                return jsonify({
                    "error": "No proxy rule found",
                    "host": host,
                    "available_rules": list(self.config.get('proxy_rules', {}).keys())
                }), 404
            
            # Build target URL
            scheme = 'https' if request.is_secure else 'http'
            path = request.full_path.split('?')[1:] or ''
            target_url = f"https://{target_domain}/{url_path}"
            if path:
                target_url += f"?{path[0]}" if path else ""
            
            logger.info(f"Proxying {host}{request.path} -> {target_url}")
            return self.proxy_request(target_url)[0]
    
    def run(self, host: str = '0.0.0.0', port: int = None, debug: bool = False):
        """Run the proxy server"""
        if port is None:
            port = self.config.get('port', 8080)
        
        https_config = self.config.get('https', {})
        
        # HTTPS 默认启用，自动生成证书
        if https_config.get('enabled', True):
            cert_path = https_config.get('cert_path')
            key_path = https_config.get('key_path')
            auto_generate = https_config.get('auto_generate', True)
            
            # 如果证书路径为空且启用自动生成，使用证书管理器
            if (not cert_path or not key_path) and auto_generate:
                cert_manager = CertManager()
                cert_path, key_path = cert_manager.get_cert_paths()
                
                # 更新配置
                https_config['cert_path'] = cert_path
                https_config['key_path'] = key_path
                self.config['https'] = https_config
                self.save_config(self.config)
            
            if cert_path and key_path and Path(cert_path).exists() and Path(key_path).exists():
                try:
                    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    ssl_context.load_cert_chain(cert_path, key_path)
                    logger.info(f"以 HTTPS 模式运行，监听 {host}:{port}")
                    logger.info(f"证书: {cert_path}")
                    self.app.run(host=host, port=port, debug=debug, ssl_context=ssl_context)
                except Exception as e:
                    logger.error(f"HTTPS 配置失败: {e}，降级为 HTTP 模式")
                    self.app.run(host=host, port=port, debug=debug)
            else:
                logger.warning("HTTPS 启用但证书文件不存在，运行 HTTP 模式")
                self.app.run(host=host, port=port, debug=debug)
        else:
            logger.info(f"以 HTTP 模式运行，监听 {host}:{port}")
            self.app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    server = ProxyServer()
    server.run(debug=True)
