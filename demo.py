"""
功能演示和测试脚本
Demonstration and Testing Script
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api"

class Colors:
    """Terminal colors"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def print_code(title, code):
    """Print code block"""
    print(f"\n{Colors.YELLOW}{title}:{Colors.END}")
    print(f"{Colors.BLUE}{code}{Colors.END}\n")

def test_connectivity():
    """Test if proxy server is running"""
    print_header("测试连接性")
    try:
        response = requests.get(f"{API_URL}/config", timeout=5)
        if response.status_code == 200:
            print_success("代理服务器正常运行")
            return True
        else:
            print_error(f"服务器返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"无法连接到代理服务器: {e}")
        print_info(f"请确保代理服务器正在运行: {BASE_URL}")
        return False

def get_config():
    """Get current configuration"""
    print_header("获取当前配置")
    try:
        response = requests.get(f"{API_URL}/config")
        config = response.json()
        
        print_success("配置获取成功")
        print(f"\n配置内容:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        return config
    except Exception as e:
        print_error(f"获取配置失败: {e}")
        return None

def add_rule(source, target):
    """Add a proxy rule"""
    print_header(f"添加规则: {source} → {target}")
    try:
        response = requests.post(
            f"{API_URL}/rules",
            json={"source": source, "target": target}
        )
        result = response.json()
        
        if result.get("status") == "success":
            print_success(f"规则添加成功")
            print(f"源域名: {Colors.CYAN}{source}{Colors.END}")
            print(f"目标域名: {Colors.GREEN}{target}{Colors.END}")
            return True
        else:
            print_error(f"添加失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"添加规则失败: {e}")
        return False

def get_rules():
    """Get all rules"""
    print_header("获取所有规则")
    try:
        response = requests.get(f"{API_URL}/rules")
        rules = response.json()
        
        if not rules:
            print_info("暂无规则")
            return rules
        
        print_success("规则列表:")
        print()
        for source, target in rules.items():
            print(f"  {Colors.CYAN}{source:30}{Colors.END} → {Colors.GREEN}{target}{Colors.END}")
        print()
        return rules
    except Exception as e:
        print_error(f"获取规则失败: {e}")
        return {}

def delete_rule(source):
    """Delete a rule"""
    print_header(f"删除规则: {source}")
    try:
        response = requests.delete(f"{API_URL}/rules/{source}")
        result = response.json()
        
        if result.get("status") == "success":
            print_success(f"规则删除成功: {source}")
            return True
        else:
            print_error(f"删除失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"删除规则失败: {e}")
        return False

def test_proxy(url):
    """Test a URL through proxy"""
    print_header(f"测试代理: {url}")
    try:
        response = requests.post(
            f"{API_URL}/test",
            json={"url": url}
        )
        result = response.json()
        
        if result.get("status") == "success":
            print_success("请求成功")
            print(f"状态码: {Colors.CYAN}{result.get('status_code')}{Colors.END}")
            print(f"\n响应预览 (前500字符):")
            print(f"{Colors.BLUE}{result.get('preview', 'N/A')}{Colors.END}")
            return True
        else:
            print_error(f"请求失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"测试失败: {e}")
        return False

def demo_basic_workflow():
    """Demonstrate basic workflow"""
    print_header("基础工作流演示")
    
    # Add multiple rules
    test_rules = [
        ("demo1.local", "example.com"),
        ("demo2.local", "httpbin.org"),
        ("api-test.local", "httpbin.org"),
    ]
    
    for source, target in test_rules:
        print_info(f"添加规则: {source} → {target}")
        add_rule(source, target)
        time.sleep(0.5)
    
    # Get all rules
    print_info("获取所有规则...")
    rules = get_rules()
    
    # Delete a rule
    if test_rules:
        print_info(f"删除规则: {test_rules[0][0]}")
        time.sleep(0.5)
        delete_rule(test_rules[0][0])
    
    # Final rules
    print_info("最终规则列表...")
    get_rules()

def demo_api_examples():
    """Show API usage examples"""
    print_header("API 使用示例")
    
    examples = [
        ("获取配置", f"curl {API_URL}/config"),
        ("添加规则", f'curl -X POST {API_URL}/rules -H "Content-Type: application/json" -d \'{{"source": "test.local", "target": "example.com"}}\''),
        ("删除规则", f"curl -X DELETE {API_URL}/rules/test.local"),
        ("测试代理", f'curl -X POST {API_URL}/test -H "Content-Type: application/json" -d \'{{"url": "https://example.com"}}\''),
    ]
    
    for title, cmd in examples:
        print_code(title, cmd)

def demo_configuration_examples():
    """Show configuration examples"""
    print_header("配置文件示例")
    
    config_examples = {
        "基础配置": {
            "proxy_rules": {
                "example.local": "example.com"
            },
            "https": {
                "enabled": False,
                "cert_path": "",
                "key_path": ""
            },
            "port": 8080,
            "log_level": "INFO"
        },
        "HTTPS 配置": {
            "proxy_rules": {
                "secure.local": "secure.example.com"
            },
            "https": {
                "enabled": True,
                "cert_path": "/path/to/cert.pem",
                "key_path": "/path/to/key.pem"
            },
            "port": 8443,
            "log_level": "INFO"
        },
        "多规则配置": {
            "proxy_rules": {
                "api.local": "api.example.com",
                "web.local": "web.example.com",
                "admin.local": "admin.example.com"
            },
            "https": {
                "enabled": False,
                "cert_path": "",
                "key_path": ""
            },
            "port": 8080,
            "log_level": "DEBUG"
        }
    }
    
    for name, config in config_examples.items():
        print_code(name, json.dumps(config, indent=2, ensure_ascii=False))

def main():
    """Main demo function"""
    print(f"\n{Colors.BOLD}HTTP/HTTPS 代理管理系统 - 功能演示{Colors.END}\n")
    
    # Check connectivity
    if not test_connectivity():
        print_error("请确保代理服务器正在运行")
        print_info("运行命令: python app.py 或 ./run.sh")
        return
    
    # Get current config
    config = get_config()
    
    # Demo basic workflow
    print_info("即将演示基础工作流...")
    time.sleep(2)
    demo_basic_workflow()
    
    # Show API examples
    print_info("显示 API 使用示例...")
    time.sleep(2)
    demo_api_examples()
    
    # Show configuration examples
    print_info("显示配置文件示例...")
    time.sleep(2)
    demo_configuration_examples()
    
    # Final message
    print_header("演示完成")
    print_success("所有演示已完成！")
    print_info("更多信息请查看:")
    print(f"  - README.md: 项目介绍和基本使用")
    print(f"  - QUICKSTART.md: 快速开始指南")
    print(f"  - ADVANCED.md: 高级功能说明")
    print(f"  - config_examples.py: 配置文件示例")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}演示已中断{Colors.END}\n")
    except Exception as e:
        print_error(f"演示过程中出错: {e}")
