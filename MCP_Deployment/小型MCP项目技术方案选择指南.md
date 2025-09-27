# 小型 MCP 项目技术方案选择：数据库 + API 访问场景

## 项目背景

**项目特点**：
- 小型 MCP 项目
- 有自己的数据库
- 需要 API Key 访问第三方服务
- 需要处理认证和状态管理

---

## 三种模式理论分析

### 1. Streamable HTTP（纯 HTTP 模式）

#### 核心理念
传统的请求-响应模式，每个 MCP 工具调用对应一个 HTTP 端点。客户端发送请求，服务器处理后直接返回结果。

#### 架构特点
- **通信模式**：同步请求-响应
- **连接方式**：短连接，每次请求独立建立连接
- **状态管理**：服务端维护用户状态（通过 API Key）
- **数据流**：单向，客户端请求 → 服务器响应

#### 优势分析
- ✅ **实现简单**：标准的 REST API 模式，开发经验丰富
- ✅ **调试便利**：可以使用任何 HTTP 客户端测试
- ✅ **缓存友好**：HTTP 标准缓存机制可以直接使用
- ✅ **负载均衡**：无状态设计便于水平扩展
- ✅ **监控成熟**：标准 HTTP 监控工具直接可用
- ✅ **安全成熟**：HTTPS、OAuth 等标准安全机制

#### 劣势分析
- ❌ **用户体验差**：长时间任务无进度反馈
- ❌ **资源浪费**：频繁建立/关闭连接
- ❌ **实时性差**：无法主动推送信息
- ❌ **超时限制**：受 HTTP 超时限制约束
- ❌ **轮询低效**：需要客户端轮询获取状态

#### 适用场景
- **快速响应工具**：处理时间 < 5秒的简单查询
- **数据库查询**：直接的 CRUD 操作
- **API 代理**：简单的第三方 API 调用封装
- **缓存友好操作**：结果可以被缓存的重复查询

---

## 详细对比分析

### 开发耗时对比

| 方案 | 基础功能 | 数据库集成 | API 集成 | 认证授权 | 总耗时 |
|------|----------|------------|----------|----------|--------|
| **Streamable HTTP** | 2天 | 1天 | 1天 | 1天 | **5天** |
| **HTTP + SSE** | 4天 | 1天 | 2天 | 2天 | **9天** |
| **STDIO** | 1天 | 0.5天 | 0.5天 | 0天 | **2天** |

### 运营成本对比（月度）

| 方案 | 服务器 | 数据库 | 监控 | 总成本 |
|------|--------|--------|------|--------|
| **Streamable HTTP** | $20 | $10 | $5 | **$35** |
| **HTTP + SSE** | $50 | $15 | $15 | **$80** |
| **STDIO** | $0 | $0 | $0 | **$0** |

### 技术适配度

| 方案 | Python | TypeScript | 推荐语言 |
|------|---------|------------|----------|
| **Streamable HTTP** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **Python** |
| **HTTP + SSE** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **TypeScript** |
| **STDIO** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | **Python** |

---

## STDIO 模式的数据库和 API 处理详解

### 1. 数据库访问策略

```python
# database_manager.py
import sqlite3
import os
from contextlib import contextmanager
from typing import List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认存储在用户主目录
            home_dir = os.path.expanduser("~")
            self.db_path = os.path.join(home_dir, ".mcp", "data.db")
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        else:
            self.db_path = db_path
        
        self.init_database()

    def init_database(self):
        """初始化数据库结构"""
        with self.get_connection() as conn:
            # 用户配置表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # API 缓存表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_cache (
                    cache_key TEXT PRIMARY KEY,
                    response_data TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 使用日志表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    parameters TEXT,
                    success BOOLEAN NOT NULL,
                    execution_time REAL,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典形式的结果
        try:
            yield conn
        finally:
            conn.close()

    def get_config(self, key: str, default: str = None) -> str:
        """获取配置值"""
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT value FROM user_config WHERE key = ?", (key,)
            ).fetchone()
            return result['value'] if result else default

    def set_config(self, key: str, value: str):
        """设置配置值"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_config (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
```

### 2. API Key 管理策略

```python
# api_manager.py
import os
import json
from typing import Optional, Dict
from cryptography.fernet import Fernet
import base64

class APIKeyManager:
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.mcp")
        
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, "api_keys.json")
        self.key_file = os.path.join(config_dir, ".key")
        
        self.cipher = self._get_or_create_cipher()

    def _get_or_create_cipher(self):
        """获取或创建加密密钥"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)  # 只有用户可读写
        
        return Fernet(key)

    def set_api_key(self, service: str, api_key: str):
        """设置 API Key"""
        keys = self._load_keys()
        
        # 加密存储
        encrypted_key = self.cipher.encrypt(api_key.encode()).decode()
        keys[service] = encrypted_key
        
        self._save_keys(keys)

    def get_api_key(self, service: str) -> Optional[str]:
        """获取 API Key"""
        # 首先尝试从环境变量获取
        env_key = os.getenv(f"{service.upper()}_API_KEY")
        if env_key:
            return env_key
        
        # 然后从配置文件获取
        keys = self._load_keys()
        encrypted_key = keys.get(service)
        
        if encrypted_key:
            try:
                return self.cipher.decrypt(encrypted_key.encode()).decode()
            except:
                return None
        
        return None

    def _load_keys(self) -> Dict[str, str]:
        """加载 API Keys"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_keys(self, keys: Dict[str, str]):
        """保存 API Keys"""
        with open(self.config_file, 'w') as f:
            json.dump(keys, f)
        os.chmod(self.config_file, 0o600)  # 只有用户可读写
```

### 3. 完整的 STDIO MCP 服务器

```python
# main.py - 完整的 STDIO MCP 服务器
import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult, ListToolsResult

from database_manager import DatabaseManager
from api_manager import APIKeyManager

class CompleteMCPServer:
    def __init__(self):
        self.server = Server("complete-mcp-server")
        self.db = DatabaseManager()
        self.api_manager = APIKeyManager()
        
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            return ListToolsResult(tools=[
                Tool(
                    name="web_search",
                    description="使用第三方 API 搜索网页",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索查询"},
                            "use_cache": {"type": "boolean", "default": True}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="set_api_key", 
                    description="设置第三方服务的 API Key",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service": {"type": "string", "description": "服务名称"},
                            "api_key": {"type": "string", "description": "API Key"}
                        },
                        "required": ["service", "api_key"]
                    }
                ),
                Tool(
                    name="query_database",
                    description="查询本地数据库",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "sql": {"type": "string", "description": "SQL查询"}
                        },
                        "required": ["sql"]
                    }
                )
            ])

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            start_time = time.time()
            
            try:
                result = None
                
                if request.name == "web_search":
                    result = await self.web_search(request.arguments)
                elif request.name == "set_api_key":
                    result = await self.set_api_key(request.arguments)
                elif request.name == "query_database":
                    result = await self.query_database(request.arguments)
                else:
                    raise ValueError(f"未知工具: {request.name}")
                
                # 记录成功使用
                execution_time = time.time() - start_time
                self.log_usage(request.name, request.arguments, True, execution_time)
                
                return result
                
            except Exception as e:
                # 记录失败使用
                execution_time = time.time() - start_time
                self.log_usage(request.name, request.arguments, False, execution_time, str(e))
                
                return CallToolResult(
                    content=[TextContent(type="text", text=f"错误: {str(e)}")]
                )

    async def web_search(self, args: dict) -> CallToolResult:
        """Web 搜索工具"""
        query = args["query"]
        use_cache = args.get("use_cache", True)
        
        # 生成缓存键
        cache_key = f"search_{hashlib.md5(query.encode()).hexdigest()}"
        
        # 检查缓存
        if use_cache:
            cached_result = self.get_cached_response(cache_key)
            if cached_result:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"[缓存结果] {cached_result}"
                    )]
                )

        # 获取搜索 API Key
        api_key = self.api_manager.get_api_key("search")
        if not api_key:
            return CallToolResult(
                content=[TextContent(
                    type="text", 
                    text="请先设置搜索 API Key: 使用 set_api_key 工具"
                )]
            )

        try:
            # 调用搜索 API (示例)
            import requests
            response = requests.get(
                "https://api.search.com/v1/search",
                params={"q": query, "key": api_key},
                timeout=10
            )
            response.raise_for_status()
            
            result_text = f"搜索结果: {response.json()}"
            
            # 缓存结果（1小时有效）
            self.cache_response(cache_key, result_text, 3600)
            
            return CallToolResult(
                content=[TextContent(type="text", text=result_text)]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"搜索失败: {str(e)}")]
            )

    async def set_api_key(self, args: dict) -> CallToolResult:
        """设置 API Key"""
        service = args["service"]
        api_key = args["api_key"]
        
        self.api_manager.set_api_key(service, api_key)
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"已设置 {service} 的 API Key"
            )]
        )

    async def query_database(self, args: dict) -> CallToolResult:
        """查询数据库"""
        sql = args["sql"].strip()
        
        # 安全检查
        if not sql.upper().startswith("SELECT"):
            return CallToolResult(
                content=[TextContent(type="text", text="只允许 SELECT 查询")]
            )

        try:
            with self.db.get_connection() as conn:
                results = conn.execute(sql).fetchall()
                result_data = [dict(row) for row in results]
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"查询结果 ({len(result_data)} 条):\n{json.dumps(result_data, indent=2, ensure_ascii=False)}"
                    )]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"查询失败: {str(e)}")]
            )

    def get_cached_response(self, cache_key: str) -> Optional[str]:
        """获取缓存的响应"""
        with self.db.get_connection() as conn:
            result = conn.execute(
                "SELECT response_data FROM api_cache WHERE cache_key = ? AND expires_at > ?",
                (cache_key, datetime.now())
            ).fetchone()
            return result['response_data'] if result else None

    def cache_response(self, cache_key: str, response_data: str, ttl_seconds: int):
        """缓存响应"""
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO api_cache (cache_key, response_data, expires_at) VALUES (?, ?, ?)",
                (cache_key, response_data, expires_at)
            )
            conn.commit()

    def log_usage(self, tool_name: str, parameters: dict, success: bool, execution_time: float, error_message: str = None):
        """记录使用日志"""
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO usage_logs (tool_name, parameters, success, execution_time, error_message) VALUES (?, ?, ?, ?, ?)",
                (tool_name, json.dumps(parameters), success, execution_time, error_message)
            )
            conn.commit()

    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

def main():
    server = CompleteMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
```

---

## 最终建议

### 🏆 **推荐方案：STDIO 模式 + Python**

**理由：**

1. **开发效率最高**：2天完成 vs 5-9天
2. **成本最低**：$0 运营成本
3. **实现最简单**：Python + MCP SDK 成熟
4. **集成最容易**：用户直接配置即可使用

### 📋 **实施步骤**

1. **第一阶段（1天）**：
   - 搭建基础 MCP 服务器框架
   - 实现数据库初始化和连接

2. **第二阶段（0.5天）**：
   - 集成 API Key 管理
   - 实现缓存机制

3. **第三阶段（0.5天）**：
   - 添加工具功能
   - 测试和调试

4. **发布阶段**：
   ```bash
   # 打包发布到 PyPI
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```

5. **用户使用**：
   ```json
   {
     "mcpServers": {
       "your-mcp": {
         "command": "python",
         "args": ["-m", "your_mcp_package"]
       }
     }
   }
   ```

### 🎯 **适合小项目的原因**

- **快速迭代**：修改代码立即生效
- **简单调试**：标准输出调试
- **用户友好**：一条命令安装使用
- **成本控制**：无服务器运营成本
- **功能完整**：数据库、API、缓存全支持

对于您的小型 MCP 项目，STDIO 模式是最明智的选择！

---

*最后更新：2025年9月27日*