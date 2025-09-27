# Python私有包 + JavaScript MCP架构

## 为什么选择Python核心 + JS MCP？

✅ **Python优势**: 数据分析、AI/ML库丰富、科学计算强大  
✅ **JavaScript优势**: MCP生态成熟、异步处理优秀、部署简单  
✅ **最佳组合**: 发挥两种语言的长处

## Python私有包平台对比

### GitHub Packages (推荐 - 免费)
```python
# setup.py
setup(
    name="your-username-core-analysis",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0", 
        "scikit-learn>=1.1.0"
    ]
)
```

### PyPI Private Index
- **Gemfury**: $7/月起
- **CloudSmith**: 免费层 + 付费
- **自建PyPI**: 使用 `devpi` (完全免费)

### 其他选择
- **GitLab Package Registry**: 免费
- **AWS CodeArtifact**: 按使用付费
- **Azure Artifacts**: 免费层

## 实现方案

### 架构A: Python HTTP API + JS MCP Client (推荐)

```
Python私有包 → FastAPI服务 → JavaScript MCP服务器
└── 核心算法      └── HTTP接口   └── MCP协议适配
```

#### Python私有包 (GitHub Packages)
```python
# src/core_analysis/__init__.py
import pandas as pd
import numpy as np
from typing import Dict, Any

class StockAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """核心分析算法 - 商业机密"""
        # 复杂的量化分析算法
        data = self._fetch_advanced_data(symbol)
        analysis = self._perform_ml_analysis(data)
        
        return {
            "symbol": symbol,
            "score": analysis["score"],
            "recommendation": analysis["action"],
            "risk_level": analysis["risk"],
            "technical_indicators": analysis["indicators"]
        }
    
    def _fetch_advanced_data(self, symbol: str):
        """私有数据源和API调用"""
        # 专有数据源逻辑
        pass
        
    def _perform_ml_analysis(self, data):
        """机器学习分析算法"""
        # 私有ML模型和算法
        pass

class PortfolioOptimizer:
    def optimize_portfolio(self, stocks: list) -> Dict[str, Any]:
        """组合优化算法"""
        # 专有算法
        pass
```

#### Python API服务器
```python
# api_server.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core_analysis import StockAnalyzer, PortfolioOptimizer
import os

app = FastAPI()
security = HTTPBearer()

def verify_license(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证用户许可证"""
    # 验证logic
    if not validate_license_key(credentials.credentials):
        raise HTTPException(401, "无效的许可证")
    return credentials.credentials

@app.post("/analyze/stock")
async def analyze_stock(
    data: dict,
    license_key: str = Depends(verify_license)
):
    analyzer = StockAnalyzer(os.getenv("API_KEY"))
    result = analyzer.analyze_stock(data["symbol"])
    return result

@app.post("/optimize/portfolio") 
async def optimize_portfolio(
    data: dict,
    license_key: str = Depends(verify_license)
):
    optimizer = PortfolioOptimizer()
    result = optimizer.optimize_portfolio(data["stocks"])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### JavaScript MCP服务器
```typescript
// src/index.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import fetch from 'node-fetch';

class PythonMcpBridge {
  private server: Server;
  private pythonApiUrl: string;
  private licenseKey: string;

  constructor() {
    this.server = new Server(
      { name: 'python-analysis-mcp', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );
    
    this.pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000';
    this.licenseKey = process.env.LICENSE_KEY || '';
    
    this.setupTools();
  }

  private setupTools() {
    this.server.setRequestHandler('tools/list', async () => ({
      tools: [
        {
          name: 'analyze/stock',
          description: '分析股票表现',
          inputSchema: {
            type: 'object',
            properties: {
              symbol: { type: 'string', description: '股票代码' }
            },
            required: ['symbol']
          }
        },
        {
          name: 'optimize/portfolio',
          description: '优化投资组合',
          inputSchema: {
            type: 'object',
            properties: {
              stocks: { 
                type: 'array', 
                items: { type: 'string' },
                description: '股票代码列表'
              }
            },
            required: ['stocks']
          }
        }
      ]
    }));

    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        const response = await fetch(`${this.pythonApiUrl}/${name}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.licenseKey}`
          },
          body: JSON.stringify(args)
        });
        
        if (!response.ok) {
          throw new Error(`Python API错误: ${response.status}`);
        }
        
        const result = await response.json();
        return {
          content: [{
            type: 'text',
            text: JSON.stringify(result, null, 2)
          }]
        };
      } catch (error) {
        return {
          content: [{
            type: 'text', 
            text: `分析失败: ${error.message}`
          }]
        };
      }
    });
  }

  async start() {
    await this.server.connect(process.stdout, process.stdin);
  }
}

// 启动服务器
const mcpServer = new PythonMcpBridge();
mcpServer.start().catch(console.error);
```

### 架构B: Python子进程调用

```typescript
// src/pythonBridge.ts
import { spawn } from 'child_process';
import * as path from 'path';

export class PythonBridge {
  private pythonPath: string;
  private scriptPath: string;

  constructor() {
    this.pythonPath = process.env.PYTHON_PATH || 'python';
    this.scriptPath = path.join(__dirname, 'python_scripts');
  }

  async analyzeStock(symbol: string, licenseKey: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const python = spawn(this.pythonPath, [
        path.join(this.scriptPath, 'analyze.py'),
        '--symbol', symbol,
        '--license', licenseKey
      ]);

      let output = '';
      let error = '';

      python.stdout.on('data', (data) => {
        output += data.toString();
      });

      python.stderr.on('data', (data) => {
        error += data.toString();
      });

      python.on('close', (code) => {
        if (code === 0) {
          try {
            resolve(JSON.parse(output));
          } catch (e) {
            reject(new Error(`JSON解析失败: ${e.message}`));
          }
        } else {
          reject(new Error(`Python脚本错误: ${error}`));
        }
      });
    });
  }
}

// MCP服务器集成
class PythonSubprocessMcp {
  private server: Server;
  private pythonBridge: PythonBridge;

  constructor() {
    this.server = new Server(
      { name: 'python-subprocess-mcp', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );
    this.pythonBridge = new PythonBridge();
    this.setupTools();
  }

  private setupTools() {
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      if (name === 'analyze_stock') {
        try {
          const result = await this.pythonBridge.analyzeStock(
            args.symbol, 
            process.env.LICENSE_KEY || ''
          );
          
          return {
            content: [{
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }]
          };
        } catch (error) {
          return {
            content: [{
              type: 'text',
              text: `分析失败: ${error.message}`
            }]
          };
        }
      }
    });
  }
}
```

```python
# python_scripts/analyze.py
import argparse
import json
import sys
import os
from core_analysis import StockAnalyzer

def validate_license(license_key):
    """验证许可证逻辑"""
    # 实现许可证验证
    return license_key and len(license_key) > 10

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', required=True)
    parser.add_argument('--license', required=True)
    
    args = parser.parse_args()
    
    # 验证许可证
    if not validate_license(args.license):
        print(json.dumps({"error": "无效许可证"}), file=sys.stderr)
        sys.exit(1)
    
    try:
        # 执行分析
        analyzer = StockAnalyzer(os.getenv("API_KEY"))
        result = analyzer.analyze_stock(args.symbol)
        
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 架构C: Python包直接集成 (Pyodide)

```typescript
// 使用pyodide在Node.js中运行Python
import { loadPyodide } from 'pyodide';

class PyodideBridge {
  private pyodide: any;
  
  async initialize() {
    this.pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
    });
    
    // 安装公开Python包
    await this.pyodide.loadPackage(['numpy', 'pandas', 'micropip']);
    
    // 安装私有包
    await this.installPrivatePackage();
  }
  
  async installPrivatePackage() {
    const micropip = this.pyodide.pyimport("micropip");
    
    // 从GitHub Packages安装私有包
    await micropip.install([
      `https://pypi.pkg.github.com/your-username/your-package/download/package.whl`
    ]);
  }
  
  async analyzeStock(symbol: string): Promise<any> {
    const pythonCode = `
import json
from core_analysis import StockAnalyzer

analyzer = StockAnalyzer("${process.env.API_KEY}")
result = analyzer.analyze_stock("${symbol}")
json.dumps(result)
    `;
    
    const result = this.pyodide.runPython(pythonCode);
    return JSON.parse(result);
  }
}

class PyodideMcpServer {
  private server: Server;
  private pyodide: PyodideBridge;

  constructor() {
    this.server = new Server(
      { name: 'pyodide-mcp', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );
    this.pyodide = new PyodideBridge();
  }

  async initialize() {
    await this.pyodide.initialize();
    this.setupTools();
  }

  private setupTools() {
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      if (name === 'analyze_stock') {
        try {
          const result = await this.pyodide.analyzeStock(args.symbol);
          return {
            content: [{
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }]
          };
        } catch (error) {
          return {
            content: [{
              type: 'text',
              text: `分析失败: ${error.message}`
            }]
          };
        }
      }
    });
  }
}
```

## Python包发布配置

### setup.py
```python
from setuptools import setup, find_packages

setup(
    name="your-username-core-analysis",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="私有股票分析核心库",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.1.0",
        "requests>=2.28.0",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    # GitHub Packages配置
    url="https://github.com/your-username/core-analysis-private",
    project_urls={
        "Bug Reports": "https://github.com/your-username/core-analysis-private/issues",
        "Source": "https://github.com/your-username/core-analysis-private",
    }
)
```

### pyproject.toml (现代配置方式)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "your-username-core-analysis"
version = "1.0.0"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
description = "私有股票分析核心库"
readme = "README.md"
license = {text = "Proprietary"}
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: Other/Proprietary License",
    "Programming Language :: Python :: 3.8",
]
dependencies = [
    "pandas>=1.5.0",
    "numpy>=1.21.0",
    "scikit-learn>=1.1.0",
    "requests>=2.28.0",
]

[project.urls]
Homepage = "https://github.com/your-username/core-analysis-private"
Repository = "https://github.com/your-username/core-analysis-private.git"
Issues = "https://github.com/your-username/core-analysis-private/issues"
```

### GitHub Actions发布 - Python包
```yaml
# .github/workflows/publish-python.yml
name: Publish Python Package to GitHub Packages

on:
  release:
    types: [created]
  push:
    tags:
      - 'v*'

jobs:
  publish-python:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
          
      - name: Build package
        run: python -m build
        
      - name: Publish to GitHub Packages
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.GITHUB_TOKEN }}
        run: |
          twine upload --repository-url https://upload.pypi.org/legacy/ \
            --username __token__ \
            --password ${{ secrets.GITHUB_TOKEN }} \
            dist/*
```

## Python包访问令牌安全方案 🔐

### 方案一：环境变量隔离（推荐）

#### 用户端配置
```bash
# 1. 用户获得授权后，在自己环境中设置
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# 2. 创建受保护的 pip.conf
mkdir -p ~/.config/pip
cat > ~/.config/pip/pip.conf << EOF
[global]
extra-index-url = https://pypi.pkg.github.com/your-username/
trusted-host = pypi.pkg.github.com
EOF

# 3. 安装时pip会自动使用环境变量中的token
pip install your-username-core-analysis
```

#### 开发者端 - 不暴露任何token信息
```python
# requirements.txt - 只包含包名，不包含认证信息
your-username-core-analysis>=1.0.0
pandas>=1.5.0
numpy>=1.21.0
```

### 方案二：动态令牌获取

#### Token管理服务
```python
# token_manager.py - 集成到Python私有包中
import os
import requests
import keyring
from typing import Optional

class TokenManager:
    def __init__(self):
        self.license_server = "https://your-license-server.com"
    
    def get_github_token(self, license_key: str) -> Optional[str]:
        """通过许可证获取临时GitHub访问令牌"""
        try:
            response = requests.post(
                f"{self.license_server}/api/github-token",
                json={"license_key": license_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # 缓存到系统密钥环，避免重复请求
                keyring.set_password(
                    "mcp-packages", 
                    "github-token", 
                    data["token"]
                )
                return data["token"]
        except Exception as e:
            print(f"获取访问令牌失败: {e}")
        
        return None
    
    def get_cached_token(self) -> Optional[str]:
        """从系统密钥环获取缓存的令牌"""
        try:
            return keyring.get_password("mcp-packages", "github-token")
        except:
            return None
    
    def validate_package_access(self, license_key: str) -> bool:
        """验证用户是否有包访问权限"""
        token = self.get_github_token(license_key)
        return token is not None
```

#### 智能安装脚本
```python
# install_private_packages.py
import subprocess
import sys
import os
from token_manager import TokenManager

def install_with_license(license_key: str):
    """使用许可证安装私有包"""
    token_manager = TokenManager()
    
    # 验证许可证并获取token
    if not token_manager.validate_package_access(license_key):
        print("❌ 无效的许可证或访问被拒绝")
        sys.exit(1)
    
    # 获取GitHub访问令牌
    github_token = token_manager.get_github_token(license_key)
    if not github_token:
        print("❌ 无法获取GitHub访问令牌")
        sys.exit(1)
    
    # 动态配置pip
    pip_conf_content = f"""[global]
extra-index-url = https://pypi.pkg.github.com/your-username/
trusted-host = pypi.pkg.github.com

[install]
index-url = https://pypi.org/simple/
extra-index-url = https://__token__:{github_token}@pypi.pkg.github.com/your-username/simple/
"""
    
    # 临时创建pip配置
    pip_conf_path = os.path.expanduser("~/.config/pip/pip.conf")
    os.makedirs(os.path.dirname(pip_conf_path), exist_ok=True)
    
    with open(pip_conf_path, "w") as f:
        f.write(pip_conf_content)
    
    try:
        # 安装私有包
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "your-username-core-analysis"
        ], check=True)
        print("✅ 私有包安装成功!")
    except subprocess.CalledProcessError:
        print("❌ 包安装失败")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python install_private_packages.py LICENSE_KEY")
        sys.exit(1)
    
    license_key = sys.argv[1]
    install_with_license(license_key)
```

### 方案三：Docker隔离（生产环境）

#### 多阶段构建Dockerfile
```dockerfile
# Dockerfile.secure-build
FROM python:3.9-slim as builder

# 构建阶段 - 只在这里使用token
ARG GITHUB_TOKEN
ARG LICENSE_KEY

WORKDIR /build

# 配置pip访问私有包
RUN echo "[global]" > /etc/pip.conf && \
    echo "extra-index-url = https://__token__:${GITHUB_TOKEN}@pypi.pkg.github.com/your-username/simple/" >> /etc/pip.conf

# 安装依赖并验证许可证
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 验证许可证
RUN python -c "
from core_analysis import StockAnalyzer
from token_manager import TokenManager
tm = TokenManager()
if not tm.validate_package_access('${LICENSE_KEY}'):
    raise Exception('Invalid license')
print('License validated successfully')
"

# 运行阶段 - 不包含任何敏感信息
FROM python:3.9-slim as runtime

WORKDIR /app

# 只复制已安装的包，不包含token信息
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY api_server.py .

# 清理敏感信息
RUN rm -f /etc/pip.conf ~/.pip/pip.conf

EXPOSE 8000
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 方案四：一次性访问令牌

#### 许可证服务器增强
```python
# enhanced_license_server.py
import jwt
import datetime
import secrets
from typing import Dict

class EnhancedLicenseServer:
    def __init__(self):
        self.one_time_tokens = {}  # 内存存储，生产环境用Redis
    
    @app.post("/api/one-time-token")
    async def generate_one_time_token(self, request: LicenseRequest):
        """生成一次性使用的GitHub访问令牌"""
        license_data = LICENSE_DB.get(request.license_key)
        
        if not license_data or not license_data["valid"]:
            raise HTTPException(401, "无效许可证")
        
        # 生成一次性token
        one_time_id = secrets.token_urlsafe(32)
        github_token = self.get_github_token_for_license(request.license_key)
        
        # 存储，5分钟后过期
        self.one_time_tokens[one_time_id] = {
            "github_token": github_token,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=5),
            "used": False
        }
        
        return {
            "one_time_token": one_time_id,
            "expires_in": 300,  # 5分钟
            "usage": "single_use_only"
        }
    
    @app.post("/api/use-one-time-token")
    async def use_one_time_token(self, one_time_token: str):
        """使用一次性令牌获取GitHub访问"""
        token_data = self.one_time_tokens.get(one_time_token)
        
        if not token_data:
            raise HTTPException(404, "令牌不存在")
        
        if token_data["used"]:
            raise HTTPException(410, "令牌已使用")
        
        if datetime.datetime.now() > token_data["expires_at"]:
            del self.one_time_tokens[one_time_token]
            raise HTTPException(410, "令牌已过期")
        
        # 标记为已使用
        token_data["used"] = True
        
        # 返回GitHub令牌
        return {
            "github_token": token_data["github_token"],
            "message": "令牌已使用，请立即安装包"
        }
```

#### 客户端使用一次性令牌
```python
# one_time_install.py
import requests
import subprocess
import tempfile
import os
import sys

def install_with_one_time_token(license_key: str):
    """使用一次性令牌安装"""
    
    # 1. 获取一次性令牌
    response = requests.post(
        "https://your-license-server.com/api/one-time-token",
        json={"license_key": license_key}
    )
    
    if response.status_code != 200:
        print("❌ 无法获取访问令牌")
        sys.exit(1)
    
    one_time_token = response.json()["one_time_token"]
    
    # 2. 使用一次性令牌获取GitHub访问
    response = requests.post(
        "https://your-license-server.com/api/use-one-time-token",
        json={"one_time_token": one_time_token}
    )
    
    if response.status_code != 200:
        print("❌ 令牌使用失败")
        sys.exit(1)
    
    github_token = response.json()["github_token"]
    
    # 3. 创建临时pip配置
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
        f.write(f"""[global]
extra-index-url = https://__token__:{github_token}@pypi.pkg.github.com/your-username/simple/
trusted-host = pypi.pkg.github.com
""")
        temp_config = f.name
    
    try:
        # 4. 使用临时配置安装
        env = os.environ.copy()
        env['PIP_CONFIG_FILE'] = temp_config
        
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "your-username-core-analysis"
        ], env=env, check=True)
        
        print("✅ 安装完成!")
        
    finally:
        # 5. 删除临时配置文件
        os.unlink(temp_config)
        print("🧹 临时文件已清理")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用: python one_time_install.py LICENSE_KEY")
        sys.exit(1)
    
    install_with_one_time_token(sys.argv[1])
```

### 方案五：代理安装服务

#### 安装代理服务
```python
# install_proxy.py
from fastapi import FastAPI, HTTPException
import subprocess
import tempfile
import os
from token_manager import TokenManager

app = FastAPI()

@app.post("/install-package")
async def proxy_install(license_key: str, package_version: str = "latest"):
    """代理安装服务 - 服务器端安装，返回wheel文件"""
    
    token_manager = TokenManager()
    
    # 验证许可证
    if not token_manager.validate_package_access(license_key):
        raise HTTPException(401, "无效许可证")
    
    # 获取GitHub令牌
    github_token = token_manager.get_github_token(license_key)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 在临时目录中下载包
        pip_conf = os.path.join(temp_dir, "pip.conf")
        with open(pip_conf, "w") as f:
            f.write(f"""[global]
extra-index-url = https://__token__:{github_token}@pypi.pkg.github.com/your-username/simple/
trusted-host = pypi.pkg.github.com
""")
        
        # 下载wheel文件
        download_dir = os.path.join(temp_dir, "wheels")
        os.makedirs(download_dir)
        
        env = os.environ.copy()
        env['PIP_CONFIG_FILE'] = pip_conf
        
        subprocess.run([
            "pip", "download", 
            "--dest", download_dir,
            "--only-binary=:all:",
            f"your-username-core-analysis{'' if package_version == 'latest' else '==' + package_version}"
        ], env=env, check=True)
        
        # 返回wheel文件内容
        wheel_files = [f for f in os.listdir(download_dir) if f.endswith('.whl')]
        if not wheel_files:
            raise HTTPException(500, "未找到wheel文件")
        
        wheel_path = os.path.join(download_dir, wheel_files[0])
        with open(wheel_path, "rb") as f:
            return {
                "filename": wheel_files[0],
                "content": f.read(),
                "install_command": f"pip install {wheel_files[0]}"
            }
```

## 用户安装和配置（更新版）

### 安装方式对比

| 方式 | 安全性 | 便利性 | 适用场景 |
|------|--------|--------|----------|
| 环境变量 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 开发环境 |
| 动态令牌 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 个人用户 |
| Docker隔离 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 生产环境 |
| 一次性令牌 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 高安全要求 |
| 代理安装 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 企业用户 |

### 推荐安装流程

#### 开发者提供的安装脚本
```bash
# install.sh - 用户友好的安装脚本
#!/bin/bash

echo "🚀 MCP私有包安装向导"
echo "====================="

# 检查许可证
read -p "请输入您的许可证密钥: " LICENSE_KEY

if [ -z "$LICENSE_KEY" ]; then
    echo "❌ 许可证密钥不能为空"
    exit 1
fi

# 选择安装方式
echo ""
echo "请选择安装方式:"
echo "1) 环境变量方式 (推荐开发者)"
echo "2) 一次性令牌方式 (推荐普通用户)" 
echo "3) Docker方式 (推荐生产环境)"

read -p "请选择 [1-3]: " INSTALL_METHOD

case $INSTALL_METHOD in
    1)
        echo "🔧 配置环境变量方式..."
        python install_private_packages.py $LICENSE_KEY
        ;;
    2)
        echo "🎫 使用一次性令牌方式..."
        python one_time_install.py $LICENSE_KEY
        ;;
    3)
        echo "🐳 准备Docker环境..."
        echo "请运行: docker build --build-arg LICENSE_KEY=$LICENSE_KEY -t my-mcp-server ."
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo "✅ 安装完成! 现在可以运行MCP服务器了"
```

### MCP服务器配置
```json
{
  "mcpServers": {
    "python-analysis": {
      "command": "node",
      "args": ["dist/index.js"],
      "env": {
        "PYTHON_API_URL": "http://localhost:8000",
        "LICENSE_KEY": "user_license_key_here",
        "PYTHON_PATH": "/usr/bin/python3",
        "API_KEY": "your_data_api_key"
      }
    }
  }
}
```

### Docker部署 (推荐生产环境)
```dockerfile
# Dockerfile.python-api
FROM python:3.9-slim

WORKDIR /app

# 安装私有包
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制API服务器代码
COPY api_server.py .

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile.mcp-server  
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY dist/ ./dist/

CMD ["node", "dist/index.js"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  python-api:
    build:
      context: .
      dockerfile: Dockerfile.python-api
    ports:
      - "8000:8000"
    environment:
      - API_KEY=${API_KEY}
    volumes:
      - ./data:/app/data

  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile.mcp-server
    environment:
      - PYTHON_API_URL=http://python-api:8000
      - LICENSE_KEY=${LICENSE_KEY}
    depends_on:
      - python-api
    stdin_open: true
    tty: true
```

## 许可证验证服务示例

### 许可证服务器
```python
# license_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import jwt
import datetime
from typing import Dict

app = FastAPI()

class LicenseRequest(BaseModel):
    license_key: str

class LicenseResponse(BaseModel):
    valid: bool
    package_access: bool
    expires_at: str
    features: list

# 模拟许可证数据库
LICENSE_DB = {
    "premium_license_123": {
        "valid": True,
        "package_access": True,
        "expires_at": "2024-12-31",
        "features": ["stock_analysis", "portfolio_optimization", "ml_models"]
    },
    "basic_license_456": {
        "valid": True, 
        "package_access": True,
        "expires_at": "2024-06-30",
        "features": ["stock_analysis"]
    }
}

@app.post("/api/validate", response_model=LicenseResponse)
async def validate_license(request: LicenseRequest):
    license_data = LICENSE_DB.get(request.license_key)
    
    if not license_data:
        return LicenseResponse(
            valid=False,
            package_access=False,
            expires_at="",
            features=[]
        )
    
    # 检查过期时间
    expires_at = datetime.datetime.strptime(license_data["expires_at"], "%Y-%m-%d")
    if expires_at < datetime.datetime.now():
        return LicenseResponse(
            valid=False,
            package_access=False,
            expires_at=license_data["expires_at"],
            features=[]
        )
    
    return LicenseResponse(**license_data)

@app.post("/api/token")
async def get_package_token(request: LicenseRequest):
    """为有效许可证生成GitHub Package访问token"""
    license_data = LICENSE_DB.get(request.license_key)
    
    if not license_data or not license_data["valid"]:
        raise HTTPException(status_code=401, detail="无效许可证")
    
    # 生成临时token (JWT)
    payload = {
        "license_key": request.license_key,
        "package_access": True,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    
    token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
    
    return {"token": token, "expires_in": 86400}  # 24小时

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

## 推荐方案总结

| 方案 | 复杂度 | 性能 | 安全性 | 扩展性 | 推荐场景 |
|------|--------|------|--------|--------|----------|
| HTTP API | 中等 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 生产环境，多用户 |
| 子进程调用 | 低 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 单用户，简单集成 |
| Pyodide集成 | 高 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 浏览器环境，演示 |

## 🚀 最佳实践

1. **开发环境**: 使用子进程调用，快速迭代
2. **测试环境**: HTTP API + Docker，接近生产
3. **生产环境**: HTTP API + Kubernetes，高可用
4. **演示环境**: Pyodide，无需Python环境

**强烈推荐HTTP API方案**：
- ✅ 性能最优
- ✅ 扩展性强  
- ✅ 可独立部署和扩缩容
- ✅ 支持负载均衡
- ✅ 便于监控和日志
- ✅ 语言分工明确

这样既能发挥Python在数据分析方面的优势，又能利用JavaScript MCP生态的成熟度！