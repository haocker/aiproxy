"""
支持SSL中间人拦截的HTTP/HTTPS代理服务器
可以劫持HTTPS连接并重新签名证书
"""
import socket
import ssl
import threading
import logging
import select
from urllib.parse import urlparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CertManager:
    """证书管理器"""
    
    def __init__(self, cert_dir: str = ".certs"):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        self.ca_cert_file = self.cert_dir / "ca-cert.pem"
        self.ca_key_file = self.cert_dir / "ca-key.pem"
        self._load_or_generate_ca()
    
    def _load_or_generate_ca(self):
        """加载或生成CA证书"""
        if self.ca_cert_file.exists() and self.ca_key_file.exists():
            with open(self.ca_key_file, 'rb') as f:
                self.ca_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            with open(self.ca_cert_file, 'rb') as f:
                self.ca_cert = x509.load_pem_x509_certificate(
                    f.read(), backend=default_backend()
                )
            logger.info("CA证书已加载")
        else:
            self._generate_ca()
    
    def _generate_ca(self):
        """生成CA证书"""
        logger.info("生成CA证书...")
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # 创建证书主体
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AIProxy CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "AIProxy Root CA"),
        ])
        
        # 创建CA证书
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=3650))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    key_encipherment=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
            .sign(private_key, hashes.SHA256(), default_backend())
        )
        
        # 保存证书和私钥
        with open(self.ca_key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(self.ca_cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        self.ca_key = private_key
        self.ca_cert = cert
        logger.info(f"CA证书已生成: {self.ca_cert_file}")
        logger.info("请在浏览器中导入CA证书: .certs/ca-cert.pem")
    
    def generate_cert_for_domain(self, domain: str):
        """为指定域名生成证书"""
        logger.info(f"为域名 {domain} 生成证书...")
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # 创建证书主体
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AIProxy"),
            x509.NameAttribute(NameOID.COMMON_NAME, domain),
        ])
        
        # 构建SAN扩展
        san_list = [x509.DNSName(domain)]
        # 添加通配符
        if '.' in domain:
            wildcard = '*' + domain[domain.index('.'):]
            san_list.append(x509.DNSName(wildcard))
        
        # 创建证书
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.ca_cert.subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .sign(self.ca_key, hashes.SHA256(), default_backend())
        )
        
        # 返回证书和私钥
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return cert_pem, key_pem


class MITMProxyServer:
    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.config = self.load_config()
        self.cert_manager = CertManager()
    
    def load_config(self):
        """加载配置"""
        config_path = Path(__file__).parent / 'config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"proxy_rules": {}, "port": 8080}
    
    def get_target_domain(self, original_domain):
        """获取映射的目标域名"""
        rules = self.config.get('proxy_rules', {})
        domain = original_domain.split(':')[0]
        if '://' in domain:
            domain = domain.split('://')[1]
        
        for key, value in rules.items():
            key_domain = key.split('://')[-1] if '://' in key else key
            if domain == key_domain or domain.endswith(key_domain):
                target = value.split('://')[-1] if '://' in value else value
                logger.info(f"域名映射: {domain} -> {target}")
                return target
        
        return domain
    
    def handle_request(self, client_socket):
        """处理客户端请求"""
        try:
            request_data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                request_data += chunk
                if b'\r\n\r\n' in request_data:
                    break
            
            request_str = request_data.decode('utf-8', errors='ignore')
            lines = request_str.split('\r\n')
            
            if not lines:
                return
            
            first_line = lines[0]
            parts = first_line.split(' ')
            
            if len(parts) < 2:
                return
            
            method = parts[0]
            url = parts[1]
            
            logger.info(f"收到请求: {method} {url[:100]}")
            
            if method.upper() == 'CONNECT':
                self.handle_connect(client_socket, url)
                return
            
            # HTTP请求处理
            if '://' not in url:
                host = None
                for line in lines[1:]:
                    if line.lower().startswith('host:'):
                        host = line.split(':', 1)[1].strip()
                        break
                if host:
                    url = f'http://{host}{url}'
            
            parsed = urlparse(url)
            if not parsed.netloc:
                return
            
            mapped_domain = self.get_target_domain(parsed.netloc)
            if mapped_domain != parsed.netloc:
                logger.info(f"应用域名映射: {parsed.netloc} -> {mapped_domain}")
                parsed = parsed._replace(netloc=mapped_domain, scheme='http')
                url = parsed.geturl()
            
            self.forward_http(client_socket, url, request_data)
            
        except Exception as e:
            logger.error(f"处理请求错误: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def handle_connect(self, client_socket, target):
        """处理HTTPS CONNECT - MITM模式"""
        try:
            if ':' in target:
                host, port = target.split(':')
                port = int(port)
            else:
                host = target
                port = 443
            
            # 应用域名映射
            original_host = host
            mapped_host = self.get_target_domain(host)
            
            if mapped_host != host:
                logger.info(f"CONNECT映射: {host}:{port} -> {mapped_host}:{port}")
                host = mapped_host
                # 对于域名映射，使用MITM模式
                self.do_mitm(client_socket, original_host, host, port)
            else:
                # 不需要映射，直接隧道
                self.do_tunnel(client_socket, host, port)
            
        except Exception as e:
            logger.error(f"CONNECT失败: {e}")
            try:
                error_response = b'HTTP/1.1 502 Bad Gateway\r\n\r\n'
                client_socket.sendall(error_response)
            except:
                pass
    
    def do_mitm(self, client_socket, original_host, target_host, port):
        """MITM模式：拦截SSL连接并重新签名"""
        cert_file = None
        key_file = None
        try:
            # 连接到目标服务器
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(10)
            target_socket.connect((target_host, port))
            
            # 建立与目标服务器的SSL连接
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            ssl_target = context.wrap_socket(target_socket, server_hostname=target_host)
            logger.info(f"MITM: 已连接到目标服务器 {target_host}:{port}")
            
            # 为原始域名生成证书
            cert_pem, key_pem = self.cert_manager.generate_cert_for_domain(original_host)
            
            # 将证书和私钥写入临时文件
            cert_file = self.cert_manager.cert_dir / f"temp_{original_host.replace('.', '_')}.crt"
            key_file = self.cert_manager.cert_dir / f"temp_{original_host.replace('.', '_')}.key"
            cert_file.write_bytes(cert_pem)
            key_file.write_bytes(key_pem)
            
            # 创建SSL上下文，使用生成的证书
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(str(cert_file), str(key_file))
            
            # 向客户端发送200响应
            response = b'HTTP/1.1 200 Connection Established\r\n\r\n'
            client_socket.sendall(response)
            
            # 升级客户端连接为SSL
            ssl_client = ssl_context.wrap_socket(client_socket, server_side=True)
            logger.info(f"MITM: 已建立与客户端的SSL连接 ({original_host})")
            
            # 双向转发数据
            self.relay_data(ssl_client, ssl_target)
            
        except Exception as e:
            logger.error(f"MITM失败: {e}")
            try:
                error_response = b'HTTP/1.1 502 Bad Gateway\r\n\r\n'
                client_socket.sendall(error_response)
            except:
                pass
        finally:
            try:
                target_socket.close()
            except:
                pass
            # 清理临时文件
            try:
                if cert_file and cert_file.exists():
                    cert_file.unlink()
                if key_file and key_file.exists():
                    key_file.unlink()
            except:
                pass
    
    def do_tunnel(self, client_socket, host, port):
        """直接隧道模式"""
        try:
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(10)
            target_socket.connect((host, port))
            
            if port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                target_socket = context.wrap_socket(target_socket, server_hostname=host)
            
            response = b'HTTP/1.1 200 Connection Established\r\n\r\n'
            client_socket.sendall(response)
            logger.info(f"隧道建立: {host}:{port}")
            
            self.relay_data(client_socket, target_socket)
            
        except Exception as e:
            logger.error(f"隧道失败: {e}")
            try:
                error_response = b'HTTP/1.1 502 Bad Gateway\r\n\r\n'
                client_socket.sendall(error_response)
            except:
                pass
        finally:
            try:
                target_socket.close()
            except:
                pass
    
    def forward_http(self, client_socket, url, original_request):
        """转发HTTP请求"""
        try:
            parsed = urlparse(url)
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(10)
            target_socket.connect((parsed.hostname, parsed.port or 80))
            target_socket.sendall(original_request)
            self.relay_data(client_socket, target_socket)
            
        except Exception as e:
            logger.error(f"转发HTTP请求失败: {e}")
            try:
                error_response = b'HTTP/1.1 502 Bad Gateway\r\n\r\n'
                client_socket.sendall(error_response)
            except:
                pass
        finally:
            try:
                target_socket.close()
            except:
                pass
    
    def relay_data(self, client_socket, target_socket):
        """双向转发数据"""
        try:
            sockets = [client_socket, target_socket]
            timeout = 10
            
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)
                
                if exceptional:
                    break
                
                if not readable:
                    continue
                
                for sock in readable:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            return
                        if sock is client_socket:
                            target_socket.sendall(data)
                        else:
                            client_socket.sendall(data)
                    except:
                        return
        except Exception as e:
            logger.debug(f"数据转发结束: {e}")
    
    def run(self):
        """启动代理服务器"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        logger.info(f"MITM代理服务器启动: {self.host}:{self.port}")
        logger.info("等待连接...")
        logger.info("重要: 请将 .certs/ca-cert.pem 导入浏览器受信任根证书颁发机构！")
        
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                logger.info(f"新连接: {client_address}")
                
                thread = threading.Thread(
                    target=self.handle_request,
                    args=(client_socket,)
                )
                thread.daemon = True
                thread.start()
                
        except KeyboardInterrupt:
            logger.info("服务器停止")
        finally:
            server_socket.close()


if __name__ == '__main__':
    config = MITMProxyServer().load_config()
    port = config.get('port', 8080)
    
    proxy = MITMProxyServer(port=port)
    proxy.run()
