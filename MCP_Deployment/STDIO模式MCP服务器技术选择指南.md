# STDIO 模式 MCP 服务器：TypeScript vs Python 选择指南

## 概述

对于传统的 stdio (标准输入输出) 模式 MCP 服务器，技术选择的考虑因素与 HTTP + SSE 模式完全不同。本文档详细对比两种技术在 stdio 模式下的优劣。

---

## STDIO 模式特点

### 工作原理
```
Claude Desktop ←→ stdin/stdout ←→ MCP Server Process
```

### 与 HTTP 模式的根本区别

| 特性 | STDIO 模式 | HTTP + SSE 模式 |
|------|------------|-----------------|
| **连接方式** | 进程间通信 | 网络连接 |
| **并发需求** | 单连接处理 | 多连接并发 |
| **状态管理** | 单会话状态 | 多用户状态 |
| **性能要求** | 响应速度 | 吞吐量 |
| **部署方式** | 本地安装 | 云端部署 |

---

## STDIO 模式技术对比

### Python 在 STDIO 模式的优势 🔥 **强烈推荐**

#### 1. **MCP SDK 官方支持**
```python
# Python MCP SDK - 官方第一支持
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 完整的类型支持和文档
server = Server("my-mcp-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="example_tool",
            description="An example tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "example_tool":
        return [TextContent(
            type="text", 
            text=f"Hello {arguments.get('message', 'World')}"
        )]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

#### 2. **生态系统优势**
```python
# 丰富的工具库生态
import requests          # HTTP 请求
import pandas as pd      # 数据处理
import numpy as np       # 数值计算
from pathlib import Path # 文件操作
import sqlite3           # 数据库
from PIL import Image    # 图像处理
import openai            # AI API
from bs4 import BeautifulSoup  # 网页解析
import json
import csv
import xml.etree.ElementTree as ET
```

#### 3. **简单直观的实现**
```python
# 完整的 Python STDIO MCP 服务器示例
import asyncio
import json
import sys
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult,
    ListResourcesRequest, ListResourcesResult,
    ListToolsRequest, ListToolsResult,
    ReadResourceRequest, ReadResourceResult,
)

class PythonStdioMCPServer:
    def __init__(self):
        self.server = Server("python-mcp-server")
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """列出所有可用工具"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="file_reader",
                        description="读取文件内容",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "文件路径"
                                }
                            },
                            "required": ["path"]
                        }
                    ),
                    Tool(
                        name="web_search",
                        description="搜索网页内容",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "搜索关键词"
                                }
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="data_analysis",
                        description="分析CSV数据",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "csv_path": {
                                    "type": "string",
                                    "description": "CSV文件路径"
                                },
                                "operation": {
                                    "type": "string",
                                    "enum": ["summary", "plot", "filter"],
                                    "description": "分析操作"
                                }
                            },
                            "required": ["csv_path", "operation"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """执行工具调用"""
            try:
                if request.name == "file_reader":
                    return await self.read_file(request.arguments)
                elif request.name == "web_search":
                    return await self.web_search(request.arguments)
                elif request.name == "data_analysis":
                    return await self.analyze_data(request.arguments)
                else:
                    raise ValueError(f"未知工具: {request.name}")
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"错误: {str(e)}")]
                )

    async def read_file(self, args: dict) -> CallToolResult:
        """读取文件工具"""
        try:
            with open(args["path"], 'r', encoding='utf-8') as f:
                content = f.read()
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"文件内容：\n{content[:1000]}..." if len(content) > 1000 else content
                )]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"读取文件失败: {str(e)}")]
            )

    async def web_search(self, args: dict) -> CallToolResult:
        """网页搜索工具"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # 模拟搜索 (实际应用中可以集成真实搜索API)
            query = args["query"]
            search_url = f"https://httpbin.org/json"  # 示例API
            
            response = requests.get(search_url, timeout=10)
            result = response.json()
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"搜索 '{query}' 的结果：\n{json.dumps(result, indent=2)}"
                )]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"搜索失败: {str(e)}")]
            )

    async def analyze_data(self, args: dict) -> CallToolResult:
        """数据分析工具"""
        try:
            import pandas as pd
            
            df = pd.read_csv(args["csv_path"])
            operation = args["operation"]
            
            if operation == "summary":
                summary = df.describe().to_string()
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"数据摘要：\n{summary}"
                    )]
                )
            elif operation == "plot":
                # 可以生成图表并返回
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="图表生成功能需要额外配置matplotlib"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text="未知操作")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"数据分析失败: {str(e)}")]
            )

    async def run(self):
        """运行服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

def main():
    server = PythonStdioMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
```

### TypeScript 在 STDIO 模式的考虑

#### 1. **MCP SDK 实现**
```typescript
// TypeScript MCP SDK - 需要更多配置
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';

export class TypeScriptStdioMCPServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'typescript-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    this.server.setRequestHandler(
      ListToolsRequestSchema,
      async () => {
        return {
          tools: [
            {
              name: 'file_operations',
              description: '文件操作工具',
              inputSchema: {
                type: 'object',
                properties: {
                  operation: {
                    type: 'string',
                    enum: ['read', 'write', 'list']
                  },
                  path: {
                    type: 'string'
                  }
                },
                required: ['operation', 'path']
              }
            } as Tool
          ]
        };
      }
    );

    this.server.setRequestHandler(
      CallToolRequestSchema,
      async (request) => {
        const { name, arguments: args } = request.params;

        switch (name) {
          case 'file_operations':
            return await this.handleFileOperation(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      }
    );
  }

  private async handleFileOperation(args: any) {
    const fs = await import('fs/promises');
    const path = await import('path');

    try {
      switch (args.operation) {
        case 'read':
          const content = await fs.readFile(args.path, 'utf-8');
          return {
            content: [
              {
                type: 'text',
                text: `文件内容：\n${content.slice(0, 1000)}${content.length > 1000 ? '...' : ''}`
              }
            ]
          };

        case 'list':
          const files = await fs.readdir(args.path);
          return {
            content: [
              {
                type: 'text',
                text: `目录内容：\n${files.join('\n')}`
              }
            ]
          };

        default:
          throw new Error(`Unknown operation: ${args.operation}`);
      }
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `操作失败: ${error.message}`
          }
        ]
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    // 防止进程退出
    process.stdin.resume();
  }
}

// 使用
const server = new TypeScriptStdioMCPServer();
server.run().catch(console.error);
```

---

## STDIO 模式详细对比

### 开发复杂度

| 方面 | Python | TypeScript |
|------|---------|------------|
| **MCP SDK 支持** | ⭐⭐⭐⭐⭐ 官方主推 | ⭐⭐⭐⭐ 完整支持 |
| **类型系统** | ⭐⭐⭐⭐ mypy 可选 | ⭐⭐⭐⭐⭐ 原生类型 |
| **调试便利性** | ⭐⭐⭐⭐⭐ 简单直观 | ⭐⭐⭐ 需要配置 |
| **错误处理** | ⭐⭐⭐⭐⭐ 异常清晰 | ⭐⭐⭐⭐ 类型安全 |
| **工具生态** | ⭐⭐⭐⭐⭐ 极其丰富 | ⭐⭐⭐ 主要是Web库 |

### 性能对比（STDIO 模式下）

| 指标 | Python | TypeScript | 说明 |
|------|---------|------------|------|
| **启动时间** | ⭐⭐⭐ 1-2秒 | ⭐⭐⭐⭐⭐ <500ms | TS 更快 |
| **内存占用** | ⭐⭐⭐ 50-100MB | ⭐⭐⭐⭐ 30-60MB | TS 更省 |
| **I/O 处理** | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐⭐⭐ 优秀 | 都很好 |
| **工具执行速度** | ⭐⭐⭐⭐ 很快 | ⭐⭐⭐⭐ 很快 | 取决于工具逻辑 |

**重要提醒**：在 STDIO 模式下，由于是单连接单会话，并发性能不是主要考虑因素！

### 实际使用场景对比

#### Python 更适合的 MCP 工具：

```python
# 1. 数据科学和分析
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn import datasets

# 2. AI 和机器学习
import openai
from transformers import pipeline
import torch

# 3. 科学计算
from scipy import stats
import sympy as sp

# 4. 网络爬虫和数据提取
import requests
from bs4 import BeautifulSoup
import scrapy

# 5. 图像和媒体处理
from PIL import Image
import cv2
import ffmpeg

# 6. 办公文档处理
import docx
from openpyxl import Workbook
import PyPDF2
```

#### TypeScript 更适合的 MCP 工具：

```typescript
// 1. API 调用和 Web 服务
import axios from 'axios';
import fetch from 'node-fetch';

// 2. 文件系统操作
import fs from 'fs/promises';
import path from 'path';

// 3. JSON/配置文件处理
import yaml from 'js-yaml';

// 4. 数据库操作
import { PrismaClient } from '@prisma/client';
import sqlite3 from 'sqlite3';

// 5. 实时通信
import { WebSocket } from 'ws';

// 6. 系统集成
import { exec } from 'child_process';
```

---

## 部署和分发对比

### Python 包分发

```bash
# 1. PyPI 分发
pip install my-mcp-server

# 2. Claude Desktop 配置
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server"]
    }
  }
}
```

**优势**：
- ✅ pip 安装简单
- ✅ 虚拟环境隔离
- ✅ 依赖管理成熟

**劣势**：
- ⚠️ Python 版本兼容性
- ⚠️ 依赖冲突问题
- ⚠️ 启动时间较长

### TypeScript 包分发

```bash
# 1. npm 分发
npm install -g my-mcp-server

# 2. Claude Desktop 配置
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "my-mcp-server"]
    }
  }
}
```

**优势**：
- ✅ npm 全局安装
- ✅ npx 即用即装
- ✅ 启动快速

**劣势**：
- ⚠️ Node.js 环境依赖
- ⚠️ 原生模块编译问题

---

## 最终建议

### 🐍 **强烈推荐 Python** 如果：

1. **工具类型**：
   - 数据分析和处理
   - AI/ML 模型调用
   - 科学计算
   - 图像/文档处理
   - 网络爬虫
   - 办公自动化

2. **团队情况**：
   - Python 开发经验丰富
   - 需要快速原型开发
   - 依赖大量 Python 库

3. **维护考虑**：
   - MCP SDK 官方主要支持
   - 社区示例丰富
   - 调试和错误处理简单

### 🟨 **考虑 TypeScript** 如果：

1. **工具类型**：
   - API 集成和调用
   - 文件系统操作
   - 数据库操作
   - 配置文件处理

2. **团队情况**：
   - Web 开发背景
   - 需要类型安全
   - 追求启动速度

### 📊 **具体建议**：

**对于大多数 MCP 工具开发，选择 Python**：

```python
# 典型的 MCP 工具开发场景
def file_analyzer_tool():
    """分析文件内容 - Python 生态丰富"""
    
def web_scraper_tool():
    """网页数据提取 - BeautifulSoup 等库成熟"""
    
def data_processor_tool():
    """数据处理 - pandas/numpy 无可替代"""
    
def ai_assistant_tool():
    """AI 功能集成 - Python AI 生态最强"""
```

**Python 是 STDIO 模式 MCP 开发的最佳选择！**

主要原因：
1. MCP SDK 官方主要支持和优化
2. 工具开发所需的库生态最丰富
3. 开发和调试体验更好
4. 社区资源和示例更多
5. 单连接场景下性能差异不显著

您计划开发什么类型的 MCP 工具？这将帮助我提供更具体的实现建议。

---

*最后更新：2025年9月26日*