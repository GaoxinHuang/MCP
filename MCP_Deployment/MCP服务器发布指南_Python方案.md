# MCP服务器发布指南 - Python方案

## 概述

本文档详细介绍如何开发、打包和发布基于Python的MCP（Model Context Protocol）服务器，包括多种发布平台的对比、定价策略和实施步骤。

---

## 开发环境准备

### 1. 环境搭建

```bash
# 创建项目目录
mkdir my-mcp-server-python
cd my-mcp-server-python

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装MCP Python SDK
pip install mcp
```

### 2. 项目结构

```
my-mcp-server-python/
├── src/
│   └── my_mcp_server/
│       ├── __init__.py
│       ├── server.py
│       └── tools/
│           ├── __init__.py
│           └── example_tool.py
├── tests/
│   └── test_server.py
├── requirements.txt
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

## MCP服务器开发

### 基础服务器实现

```python
# src/my_mcp_server/server.py
import asyncio
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyMCPServer:
    def __init__(self):
        self.server = Server("my-mcp-server")
        self.setup_handlers()

    def setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """列出所有可用的工具"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="hello_world",
                        description="返回Hello World消息",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "要问候的名字"
                                }
                            },
                            "required": ["name"]
                        }
                    ),
                    Tool(
                        name="calculate",
                        description="执行基本数学运算",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "enum": ["add", "subtract", "multiply", "divide"],
                                    "description": "要执行的运算"
                                },
                                "a": {
                                    "type": "number",
                                    "description": "第一个数字"
                                },
                                "b": {
                                    "type": "number", 
                                    "description": "第二个数字"
                                }
                            },
                            "required": ["operation", "a", "b"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """执行工具调用"""
            if request.name == "hello_world":
                name = request.arguments.get("name", "World")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Hello, {name}! 这是来自MCP服务器的问候。"
                        )
                    ]
                )
            
            elif request.name == "calculate":
                operation = request.arguments["operation"]
                a = request.arguments["a"]
                b = request.arguments["b"]
                
                result = 0
                if operation == "add":
                    result = a + b
                elif operation == "subtract":
                    result = a - b
                elif operation == "multiply":
                    result = a * b
                elif operation == "divide":
                    if b == 0:
                        return CallToolResult(
                            content=[TextContent(type="text", text="错误：除数不能为零")]
                        )
                    result = a / b
                
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"{a} {operation} {b} = {result}"
                        )
                    ]
                )
            else:
                raise ValueError(f"未知工具: {request.name}")

        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """列出可用资源"""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="config://settings",
                        name="服务器配置",
                        description="MCP服务器的配置信息",
                        mimeType="application/json"
                    )
                ]
            )

        @self.server.read_resource()
        async def read_resource(request: ReadResourceRequest) -> ReadResourceResult:
            """读取资源内容"""
            if request.uri == "config://settings":
                config = {
                    "server_name": "my-mcp-server",
                    "version": "1.0.0",
                    "capabilities": ["tools", "resources"]
                }
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=str(config)
                        )
                    ]
                )
            else:
                raise ValueError(f"未知资源: {request.uri}")

    async def run(self):
        """运行MCP服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

def main():
    """主函数"""
    server = MyMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
```

### 配置文件

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-mcp-server"
dynamic = ["version"]
description = "一个示例MCP服务器"
readme = "README.md"
license = "MIT"
authors = [
    { name = "Your Name", email = "your.email@example.com" },
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.9"
dependencies = [
    "mcp>=0.1.0",
    "pydantic>=2.0.0",
    "asyncio",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0",
    "isort>=5.0",
    "mypy>=1.0",
    "pre-commit>=3.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/my-mcp-server"
Documentation = "https://github.com/yourusername/my-mcp-server#readme"
Repository = "https://github.com/yourusername/my-mcp-server"
Issues = "https://github.com/yourusername/my-mcp-server/issues"

[project.scripts]
my-mcp-server = "my_mcp_server.server:main"

[tool.hatch.version]
path = "src/my_mcp_server/__init__.py"

[tool.hatch.build.targets.wheel]
packages = ["src/my_mcp_server"]
```

```txt
# requirements.txt
mcp>=0.1.0
pydantic>=2.0.0
```

## 发布平台对比

### 1. PyPI (Python Package Index) 🔥 **主推**

**优势：**
- Python生态系统的标准包管理器
- 完全免费
- 全球CDN分发
- 良好的版本管理
- pip原生支持

**发布流程：**
```bash
# 安装构建工具
pip install build twine

# 构建包
python -m build

# 上传到PyPI
twine upload dist/*
```

**价格：** 完全免费

**使用方式：**
```bash
# 用户安装
pip install my-mcp-server

# Claude Desktop配置
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server.server"]
    }
  }
}
```

---

### 2. GitHub Packages 🔥 **推荐**

**优势：**
- 与GitHub仓库紧密集成
- 私有包支持
- Actions自动化发布
- 企业级安全性

**发布流程：**
```yaml
# .github/workflows/publish.yml
name: Publish Python Package

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

**价格：** 
- 公共包：免费
- 私有包：GitHub Pro ($4/月) 或团队方案

---

### 3. Anaconda (Conda-forge)

**优势：**
- 科学计算社区认可度高
- 依赖管理优秀
- 跨平台二进制分发

**发布流程：**
```yaml
# meta.yaml
{% set name = "my-mcp-server" %}
{% set version = "1.0.0" %}

package:
  name: {{ name|lower }}
  version: {{ version }}

source:
  url: https://pypi.io/packages/source/{{ name[0] }}/{{ name }}/{{ name }}-{{ version }}.tar.gz
  sha256: YOUR_SHA256_HERE

build:
  noarch: python
  script: {{ PYTHON }} -m pip install . -vv
  number: 0

requirements:
  host:
    - python >=3.9
    - pip
  run:
    - python >=3.9
    - mcp >=0.1.0

test:
  imports:
    - my_mcp_server
  commands:
    - my-mcp-server --help

about:
  home: https://github.com/yourusername/my-mcp-server
  license: MIT
  summary: A sample MCP server
```

**价格：** 免费，但需要社区审核

---

### 4. Docker Hub

**优势：**
- 容器化部署
- 跨平台兼容
- 易于部署和分发

**Dockerfile示例：**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY pyproject.toml .

RUN pip install -e .

EXPOSE 8000

CMD ["my-mcp-server"]
```

**发布流程：**
```bash
# 构建镜像
docker build -t yourusername/my-mcp-server:latest .

# 推送到Docker Hub
docker push yourusername/my-mcp-server:latest
```

**价格：**
- 公共镜像：免费
- 私有镜像：$5/月起

## 定价策略建议

### 免费发布方案

**基础功能MCP服务器**
- 平台：PyPI + GitHub
- 成本：$0
- 适用：开源项目、社区贡献、个人学习

### 收费服务方案

#### 1. 订阅制SaaS模式

**定价层级：**
```
基础版：$9/月
- 支持5个MCP服务器实例
- 社区支持
- 基础API限制：1000次/天

专业版：$29/月  
- 支持20个MCP服务器实例
- 优先技术支持
- 高级API限制：10000次/天
- 自定义域名

企业版：$99/月
- 无限MCP服务器实例
- 专属技术支持
- 无API限制
- 私有部署选项
- SLA保证
```

#### 2. 按使用量计费

**API调用计费：**
```
前1000次：免费
1,001-10,000次：$0.01/次
10,001-100,000次：$0.005/次
100,000+次：$0.002/次
```

#### 3. 一次性授权

**软件许可：**
```
个人许可：$99
商业许可：$299
企业许可：$999
源码许可：$2999
```

## 营销和推广

### 1. 技术社区推广

**平台列表：**
- **GitHub**：开源项目，获得Star和Fork
- **Reddit**：r/MachineLearning, r/Python
- **Hacker News**：技术新闻分享
- **Dev.to**：技术博客文章
- **Medium**：深度技术文章

**内容策略：**
```
第1周：发布开源项目
第2周：撰写技术博客
第3周：社区分享和讨论
第4周：收集反馈，优化产品
```

### 2. 文档和教程

**必备文档：**
- README.md（项目介绍）
- API文档（Swagger/OpenAPI）
- 快速开始指南
- 最佳实践
- 故障排查指南

**示例教程：**
```markdown
# 快速开始

## 安装
`pip install my-mcp-server`

## 配置Claude Desktop
将以下配置添加到你的Claude Desktop配置文件：
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server.server"]
    }
  }
}

## 使用示例
1. 重启Claude Desktop
2. 在对话中输入：请使用hello_world工具向"张三"问好
3. 观察MCP服务器的响应
```

## 技术支持和维护

### 1. 版本管理策略

**语义化版本控制：**
- 主版本（1.0.0）：破坏性更改
- 次版本（1.1.0）：新功能添加
- 修订版（1.1.1）：bug修复

**发布流程：**
```bash
# 更新版本号
vim src/my_mcp_server/__init__.py

# 创建git标签
git tag -a v1.0.1 -m "Release version 1.0.1"

# 推送标签触发自动发布
git push origin v1.0.1
```

### 2. 用户支持

**支持渠道：**
- GitHub Issues（技术问题）
- Discord/Slack社区
- 邮件支持（付费用户）
- 在线文档和FAQ

**响应时间承诺：**
```
免费用户：7天内回复
付费用户：24小时内回复
企业用户：4小时内回复
紧急问题：1小时内回复
```

## 成本分析

### 开发成本

| 项目 | 工时 | 成本 |
|------|------|------|
| 基础MCP服务器开发 | 40小时 | $4,000 |
| 文档和教程编写 | 20小时 | $2,000 |
| 测试和调试 | 20小时 | $2,000 |
| 包装和发布 | 10小时 | $1,000 |
| **总计** | **90小时** | **$9,000** |

### 运营成本（月度）

| 项目 | 免费版 | 付费版 |
|------|--------|--------|
| 服务器托管 | $0 | $50-200 |
| 域名和SSL | $0 | $15 |
| 监控和日志 | $0 | $25 |
| 客户支持工具 | $0 | $50 |
| **总计** | **$0** | **$140-290** |

### 收入预期

**保守估计：**
```
月活跃用户：1000
付费转化率：5%
平均客单价：$29
月收入：$1,450
年收入：$17,400
```

**乐观估计：**
```
月活跃用户：10000  
付费转化率：10%
平均客单价：$49
月收入：$49,000
年收入：$588,000
```

## 法律和合规

### 开源许可证选择

**MIT许可证（推荐）**
```
优势：
- 最宽松的许可证
- 商业友好
- 社区接受度高

适用：希望广泛采用的项目
```

**Apache 2.0许可证**
```
优势：
- 包含专利保护
- 企业友好
- 贡献者协议

适用：企业级项目
```

### 服务条款

**必须包含的条款：**
- 服务范围和限制
- 用户数据处理
- 知识产权声明
- 免责声明
- 争议解决机制

## 总结和建议

### 推荐发布路径

**阶段1：开源发布（0-3个月）**
1. 在GitHub开源发布
2. 发布到PyPI
3. 撰写技术博客
4. 社区推广

**阶段2：商业化探索（3-6个月）**
1. 推出付费版本
2. 企业客户开发
3. 技术支持服务
4. 高级功能开发

**阶段3：规模化运营（6个月以上）**
1. 多产品线扩展
2. 合作伙伴计划
3. 企业级部署
4. 国际化发展

### 成功关键因素

1. **产品质量**：稳定性和性能是基础
2. **文档完善**：降低用户使用门槛
3. **社区建设**：活跃的用户社区
4. **持续创新**：跟上技术发展趋势
5. **商业模式**：可持续的盈利模式

---

*最后更新：2025年9月26日*