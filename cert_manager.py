"""
自动 HTTPS 证书生成与管理模块
自动生成自签名证书，支持多域名
"""
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)


class CertManager:
    """HTTPS 证书管理器"""
    
    def __init__(self, cert_dir: str = "./.certs"):
        """
        初始化证书管理器
        
        Args:
            cert_dir: 证书存储目录
        """
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        self.cert_file = self.cert_dir / "cert.pem"
        self.key_file = self.cert_dir / "key.pem"
        
    def cert_exists(self) -> bool:
        """检查证书是否存在"""
        return self.cert_file.exists() and self.key_file.exists()
    
    def generate_certificate(self, domains: list = None) -> tuple:
        """
        生成自签名证书
        
        Args:
            domains: 域名列表，如果为 None 则使用默认值
            
        Returns:
            (cert_path, key_path) 元组
        """
        if domains is None:
            domains = [
                "localhost",
                "127.0.0.1",
                "*.local",
                "*.localhost"
            ]
        
        logger.info(f"生成自签名证书，域名: {domains}")
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # 创建证书主体
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AIProxy"),
            x509.NameAttribute(NameOID.COMMON_NAME, domains[0]),
        ])
        
        # 构建 SAN 扩展（主题替代名称）
        san_list = [x509.DNSName(domain) for domain in domains]
        
        # 创建证书
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
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
            .sign(private_key, hashes.SHA256(), default_backend())
        )
        
        # 保存私钥
        with open(self.key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # 保存证书
        with open(self.cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        logger.info(f"证书已保存: {self.cert_file}")
        logger.info(f"私钥已保存: {self.key_file}")
        
        return str(self.cert_file), str(self.key_file)
    
    def get_cert_paths(self) -> tuple:
        """
        获取证书路径，如果不存在则生成
        
        Returns:
            (cert_path, key_path) 元组
        """
        if not self.cert_exists():
            logger.info("证书不存在，正在生成...")
            return self.generate_certificate()
        
        logger.info(f"使用现有证书: {self.cert_file}")
        return str(self.cert_file), str(self.key_file)
    
    def update_certificate(self, domains: list = None):
        """
        更新证书（删除旧证书并生成新证书）
        
        Args:
            domains: 新域名列表
        """
        logger.info("更新证书...")
        
        # 删除旧证书
        if self.cert_file.exists():
            self.cert_file.unlink()
        if self.key_file.exists():
            self.key_file.unlink()
        
        # 生成新证书
        return self.generate_certificate(domains)
