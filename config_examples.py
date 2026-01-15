"""
Advanced configuration examples for the HTTP/HTTPS Proxy
"""

# Example 1: Basic HTTP proxy configuration
BASIC_HTTP_CONFIG = {
    "proxy_rules": {
        "local.example": "api.example.com",
        "dev.local": "dev.example.com"
    },
    "https": {
        "enabled": False,
        "cert_path": "",
        "key_path": ""
    },
    "port": 8080,
    "log_level": "INFO"
}

# Example 2: HTTPS proxy with self-signed certificate
HTTPS_CONFIG = {
    "proxy_rules": {
        "local.example": "api.example.com",
        "secure.local": "secure.example.com"
    },
    "https": {
        "enabled": True,
        "cert_path": "./certs/cert.pem",
        "key_path": "./certs/key.pem"
    },
    "port": 8443,
    "log_level": "INFO"
}

# Example 3: Advanced proxy rules with multiple services
ADVANCED_CONFIG = {
    "proxy_rules": {
        "api.local": "api.production.com",
        "admin.local": "admin.production.com",
        "cdn.local": "cdn.production.com",
        "ws.local": "websocket.production.com",
        "sse.local": "events.production.com",
        "auth.local": "auth.production.com",
        "db.local": "database.production.com",
        "cache.local": "redis.production.com"
    },
    "https": {
        "enabled": False,
        "cert_path": "",
        "key_path": ""
    },
    "port": 8080,
    "log_level": "DEBUG"
}

# Configuration documentation
CONFIG_DOCS = """
# Configuration File Documentation

## proxy_rules
A dictionary mapping source domains (keys) to target domains (values).

Examples:
- "example.local" -> "example.com" : Redirect local domain to production
- "api.local" -> "api.example.com" : Redirect local API to production API
- "dev.local" -> "dev.example.com" : Redirect local dev environment

## https
HTTPS configuration object.

enabled (boolean):
  - true: Enable HTTPS
  - false: Disable HTTPS (HTTP only)

cert_path (string):
  Path to the SSL certificate file (.pem format)
  Example: "/etc/ssl/certs/cert.pem"

key_path (string):
  Path to the SSL private key file (.pem format)
  Example: "/etc/ssl/certs/key.pem"

## port
Port number for the proxy server to listen on.
Default: 8080
Range: 1-65535

## log_level
Logging level for the application.

Available levels:
  - DEBUG: Most verbose, includes all debug information
  - INFO: Standard logging, includes info and higher
  - WARNING: Shows warnings and errors
  - ERROR: Shows only errors

Default: INFO

## Usage Tips

1. Domain Mapping:
   - Source domain should be resolvable on your system (add to /etc/hosts)
   - Target domain should be a real, accessible domain
   - Multiple services can be routed through the same proxy

2. HTTPS Setup:
   - Generate self-signed certificate with OpenSSL:
     $ openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   - Include full absolute paths in configuration
   - Ensure certificate matches source domain for browser compatibility

3. Performance:
   - Adjust log level to WARNING or ERROR in production
   - Monitor port availability before starting
   - Use DEBUG level only for troubleshooting

4. Security:
   - Never expose proxy to untrusted networks
   - Use HTTPS for sensitive applications
   - Validate proxy rules before using in production
   - Implement authentication if needed at the target server
"""

if __name__ == "__main__":
    print(CONFIG_DOCS)
