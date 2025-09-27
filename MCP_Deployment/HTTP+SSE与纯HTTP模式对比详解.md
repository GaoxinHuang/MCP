# HTTP + SSE vs 纯 HTTP 模式对比详解

## 概述

本文档详细对比 HTTP + SSE 模式和纯 HTTP 模式在 MCP 服务器实现中的区别，包括架构设计、代码实现、性能特点和使用场景。

---

## 核心区别对比

### 通信模式差异

```
纯 HTTP 模式：
Client ──Request──> Server
Client <─Response── Server
（每次都是独立的请求-响应）

HTTP + SSE 模式：  
Client ──Request──> Server
Client <═══SSE═══ Server
（保持长连接，服务器可主动推送）
```

### 连接特性对比

| 特性 | 纯 HTTP | HTTP + SSE |
|------|---------|------------|
| **连接类型** | 短连接 | 长连接 |
| **服务器推送** | 不支持 | 支持 |
| **实时性** | 需要轮询 | 真实时 |
| **连接开销** | 每次重新建立 | 一次建立多次使用 |
| **状态管理** | 无状态 | 有状态 |
| **复杂度** | 简单 | 中等 |

---

## 代码实现对比

### 1. 纯 HTTP 模式实现

```typescript
// 纯 HTTP MCP 服务器
import express from 'express';
import cors from 'cors';

interface MCPRequest {
  method: string;
  params?: any;
}

interface MCPResponse {
  result?: any;
  error?: {
    code: number;
    message: string;
  };
}

export class PureHTTPMCPServer {
  private app: express.Application;
  private tools: Map<string, Function> = new Map();

  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupTools();
  }

  private setupMiddleware() {
    this.app.use(cors());
    this.app.use(express.json());
    
    // 请求日志
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
      next();
    });
  }

  private setupRoutes() {
    // 健康检查
    this.app.get('/health', (req, res) => {
      res.json({ status: 'healthy', timestamp: new Date().toISOString() });
    });

    // 列出工具 - 同步响应
    this.app.get('/api/tools', (req, res) => {
      const tools = Array.from(this.tools.keys()).map(name => ({
        name,
        description: `Tool: ${name}`,
        inputSchema: {
          type: 'object',
          properties: {}
        }
      }));
      
      res.json({ tools });
    });

    // 调用工具 - 同步响应
    this.app.post('/api/tools/:toolName', async (req, res) => {
      try {
        const { toolName } = req.params;
        const args = req.body;

        const tool = this.tools.get(toolName);
        if (!tool) {
          return res.status(404).json({
            error: { code: -32601, message: `Tool ${toolName} not found` }
          });
        }

        // 直接等待结果并返回
        const result = await tool(args);
        res.json({ 
          result: { 
            content: [{ type: 'text', text: result }] 
          } 
        });

      } catch (error) {
        res.status(500).json({
          error: { code: -32603, message: error.message }
        });
      }
    });

    // MCP 协议端点 - 处理标准 MCP 请求
    this.app.post('/api/mcp', async (req, res) => {
      try {
        const mcpRequest: MCPRequest = req.body;
        const response = await this.processMCPRequest(mcpRequest);
        res.json(response);
      } catch (error) {
        res.status(500).json({
          error: { code: -32603, message: error.message }
        });
      }
    });
  }

  private async processMCPRequest(request: MCPRequest): Promise<MCPResponse> {
    switch (request.method) {
      case 'tools/list':
        return {
          result: {
            tools: Array.from(this.tools.keys()).map(name => ({
              name,
              description: `Tool: ${name}`,
              inputSchema: { type: 'object', properties: {} }
            }))
          }
        };

      case 'tools/call':
        const { name, arguments: args } = request.params;
        const tool = this.tools.get(name);
        
        if (!tool) {
          return {
            error: { code: -32601, message: `Tool ${name} not found` }
          };
        }

        const result = await tool(args);
        return {
          result: { content: [{ type: 'text', text: result }] }
        };

      default:
        return {
          error: { code: -32601, message: `Method ${request.method} not found` }
        };
    }
  }

  private setupTools() {
    this.tools.set('calculate', async (args: any) => {
      const { operation, a, b } = args;
      switch (operation) {
        case 'add': return `${a} + ${b} = ${a + b}`;
        case 'subtract': return `${a} - ${b} = ${a - b}`;
        default: throw new Error('Unknown operation');
      }
    });

    this.tools.set('get_time', async () => {
      return `当前时间：${new Date().toLocaleString('zh-CN')}`;
    });
  }

  public start(port: number = 3000) {
    this.app.listen(port, () => {
      console.log(`Pure HTTP MCP Server running on port ${port}`);
    });
  }
}
```

### 2. HTTP + SSE 模式实现

```typescript
// HTTP + SSE MCP 服务器
import express from 'express';
import cors from 'cors';
import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';

interface SSEConnection {
  id: string;
  response: express.Response;
  userId?: string;
  lastActivity: Date;
}

interface MCPRequest {
  id: string;
  method: string;
  params?: any;
}

export class HTTPSSEMCPServer extends EventEmitter {
  private app: express.Application;
  private connections: Map<string, SSEConnection> = new Map();
  private tools: Map<string, Function> = new Map();
  private pendingRequests: Map<string, any> = new Map();

  constructor() {
    super();
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupTools();
  }

  private setupMiddleware() {
    this.app.use(cors());
    this.app.use(express.json());
  }

  private setupRoutes() {
    // 健康检查
    this.app.get('/health', (req, res) => {
      res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        activeConnections: this.connections.size
      });
    });

    // SSE 连接端点 - 建立长连接
    this.app.get('/api/connect', this.handleSSEConnection.bind(this));

    // HTTP MCP 请求端点 - 异步处理
    this.app.post('/api/mcp', this.handleMCPRequest.bind(this));

    // 直接 HTTP 工具调用（兼容模式）
    this.app.post('/api/tools/:toolName', async (req, res) => {
      try {
        const { toolName } = req.params;
        const args = req.body;

        const tool = this.tools.get(toolName);
        if (!tool) {
          return res.status(404).json({
            error: { code: -32601, message: `Tool ${toolName} not found` }
          });
        }

        const result = await tool(args);
        res.json({ 
          result: { 
            content: [{ type: 'text', text: result }] 
          } 
        });

      } catch (error) {
        res.status(500).json({
          error: { code: -32603, message: error.message }
        });
      }
    });
  }

  // 核心区别1：SSE 连接处理
  private handleSSEConnection(req: express.Request, res: express.Response) {
    const connectionId = uuidv4();
    
    // 设置 SSE 头部
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control'
    });

    // 创建连接记录
    const connection: SSEConnection = {
      id: connectionId,
      response: res,
      userId: req.query.userId as string,
      lastActivity: new Date()
    };

    this.connections.set(connectionId, connection);

    // 发送连接成功消息
    this.sendSSEMessage(connectionId, 'connected', { 
      connectionId,
      serverTime: new Date().toISOString()
    });

    console.log(`SSE connection established: ${connectionId}`);

    // 处理客户端断开连接
    req.on('close', () => {
      this.connections.delete(connectionId);
      console.log(`SSE connection closed: ${connectionId}`);
    });

    req.on('error', (error) => {
      console.error(`SSE connection error: ${connectionId}`, error);
      this.connections.delete(connectionId);
    });

    // 定期发送心跳
    const heartbeat = setInterval(() => {
      if (this.connections.has(connectionId)) {
        this.sendSSEMessage(connectionId, 'heartbeat', { 
          timestamp: Date.now() 
        });
      } else {
        clearInterval(heartbeat);
      }
    }, 30000); // 30秒心跳
  }

  // 核心区别2：异步消息处理
  private async handleMCPRequest(req: express.Request, res: express.Response) {
    try {
      const mcpRequest: MCPRequest = req.body;
      const connectionId = req.headers['x-connection-id'] as string;

      if (!connectionId || !this.connections.has(connectionId)) {
        return res.status(400).json({ error: 'Invalid connection ID' });
      }

      // 更新连接活动时间
      const connection = this.connections.get(connectionId)!;
      connection.lastActivity = new Date();

      // 存储待处理请求
      this.pendingRequests.set(mcpRequest.id, {
        connectionId,
        timestamp: Date.now()
      });

      // 异步处理请求
      this.processRequestAsync(mcpRequest, connectionId);
      
      // 立即返回确认
      res.json({ 
        status: 'accepted', 
        requestId: mcpRequest.id,
        message: 'Request is being processed'
      });

    } catch (error) {
      console.error('MCP request error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }

  // 核心区别3：异步请求处理
  private async processRequestAsync(request: MCPRequest, connectionId: string) {
    try {
      let response: any;

      switch (request.method) {
        case 'tools/list':
          response = {
            id: request.id,
            result: {
              tools: Array.from(this.tools.keys()).map(name => ({
                name,
                description: `Tool: ${name}`,
                inputSchema: { type: 'object', properties: {} }
              }))
            }
          };
          break;

        case 'tools/call':
          const { name, arguments: args } = request.params;
          const tool = this.tools.get(name);
          
          if (!tool) {
            response = {
              id: request.id,
              error: { code: -32601, message: `Tool ${name} not found` }
            };
          } else {
            // 模拟长时间运行的工具
            await this.simulateLongRunningTask(request.id, connectionId);
            
            const result = await tool(args);
            response = {
              id: request.id,
              result: { content: [{ type: 'text', text: result }] }
            };
          }
          break;

        default:
          response = {
            id: request.id,
            error: { code: -32601, message: `Method ${request.method} not found` }
          };
      }

      // 通过 SSE 发送最终响应
      this.sendSSEMessage(connectionId, 'mcp-response', response);
      
      // 清理待处理请求
      this.pendingRequests.delete(request.id);

    } catch (error) {
      const errorResponse = {
        id: request.id,
        error: { code: -32603, message: `Internal error: ${error.message}` }
      };
      
      this.sendSSEMessage(connectionId, 'mcp-response', errorResponse);
      this.pendingRequests.delete(request.id);
    }
  }

  // 核心区别4：进度更新能力
  private async simulateLongRunningTask(requestId: string, connectionId: string) {
    // 发送进度更新（只有 SSE 模式可以做到）
    this.sendSSEMessage(connectionId, 'progress', {
      requestId,
      status: 'processing',
      progress: 0.2,
      message: '开始处理请求...'
    });

    await new Promise(resolve => setTimeout(resolve, 1000));

    this.sendSSEMessage(connectionId, 'progress', {
      requestId,
      status: 'processing', 
      progress: 0.6,
      message: '正在执行工具...'
    });

    await new Promise(resolve => setTimeout(resolve, 1000));

    this.sendSSEMessage(connectionId, 'progress', {
      requestId,
      status: 'processing',
      progress: 0.9,
      message: '准备返回结果...'
    });

    await new Promise(resolve => setTimeout(resolve, 500));
  }

  // 核心区别5：服务器推送消息
  private sendSSEMessage(connectionId: string, type: string, data: any) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    const message = {
      type,
      data,
      timestamp: new Date().toISOString()
    };

    try {
      connection.response.write(`data: ${JSON.stringify(message)}\n\n`);
    } catch (error) {
      console.error(`Failed to send SSE message to ${connectionId}:`, error);
      this.connections.delete(connectionId);
    }
  }

  private setupTools() {
    // 快速工具
    this.tools.set('get_time', async () => {
      return `当前时间：${new Date().toLocaleString('zh-CN')}`;
    });

    // 慢速工具（演示进度更新）
    this.tools.set('slow_calculation', async (args: any) => {
      const { seconds = 3 } = args;
      
      for (let i = 0; i < seconds; i++) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      return `经过 ${seconds} 秒的复杂计算，结果是：${Math.random()}`;
    });

    this.tools.set('calculate', async (args: any) => {
      const { operation, a, b } = args;
      
      // 模拟计算延迟
      await new Promise(resolve => setTimeout(resolve, 100));
      
      switch (operation) {
        case 'add': return `${a} + ${b} = ${a + b}`;
        case 'subtract': return `${a} - ${b} = ${a - b}`;
        case 'multiply': return `${a} × ${b} = ${a * b}`;
        case 'divide': 
          if (b === 0) throw new Error('Division by zero');
          return `${a} ÷ ${b} = ${a / b}`;
        default: throw new Error('Unknown operation');
      }
    });
  }

  // 连接管理
  public broadcastMessage(type: string, data: any) {
    for (const [id, connection] of this.connections) {
      this.sendSSEMessage(id, type, data);
    }
  }

  public getConnectionStats() {
    return {
      totalConnections: this.connections.size,
      pendingRequests: this.pendingRequests.size,
      connectionsPerUser: this.getConnectionsPerUser()
    };
  }

  private getConnectionsPerUser(): Record<string, number> {
    const stats: Record<string, number> = {};
    for (const connection of this.connections.values()) {
      if (connection.userId) {
        stats[connection.userId] = (stats[connection.userId] || 0) + 1;
      }
    }
    return stats;
  }

  public start(port: number = 3000) {
    this.app.listen(port, () => {
      console.log(`HTTP + SSE MCP Server running on port ${port}`);
    });

    // 清理不活跃连接
    setInterval(() => {
      this.cleanupInactiveConnections();
    }, 60000);
  }

  private cleanupInactiveConnections() {
    const now = new Date();
    const timeout = 5 * 60 * 1000; // 5分钟超时

    for (const [id, connection] of this.connections) {
      if (now.getTime() - connection.lastActivity.getTime() > timeout) {
        try {
          connection.response.end();
        } catch (error) {
          // 忽略错误
        }
        this.connections.delete(id);
        console.log(`Cleaned up inactive connection: ${id}`);
      }
    }
  }
}
```

---

## 客户端调用方式对比

### 纯 HTTP 客户端

```typescript
// 纯 HTTP 客户端 - 简单但功能有限
export class PureHTTPClient {
  constructor(private baseUrl: string) {}

  // 同步调用工具
  async callTool(name: string, args: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/tools/${name}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(args)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    if (result.error) {
      throw new Error(result.error.message);
    }

    return result.result;
  }

  // MCP 协议调用
  async sendMCPRequest(method: string, params?: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/mcp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ method, params })
    });

    const result = await response.json();
    if (result.error) {
      throw new Error(result.error.message);
    }

    return result.result;
  }

  // 获取工具列表
  async getTools(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/tools`);
    const result = await response.json();
    return result.tools;
  }
}
```

### HTTP + SSE 客户端

```typescript
// HTTP + SSE 客户端 - 功能丰富
import { EventSource } from 'eventsource';

export class HTTPSSEClient extends EventEmitter {
  private eventSource: EventSource | null = null;
  private connectionId: string | null = null;
  private pendingRequests: Map<string, {
    resolve: Function;
    reject: Function;
    onProgress?: (progress: any) => void;
  }> = new Map();

  constructor(private baseUrl: string, private userId?: string) {
    super();
  }

  // 建立 SSE 连接
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = this.userId 
        ? `${this.baseUrl}/api/connect?userId=${this.userId}`
        : `${this.baseUrl}/api/connect`;

      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log('SSE connection established');
      };

      this.eventSource.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleSSEMessage(message);
          
          if (message.type === 'connected') {
            this.connectionId = message.data.connectionId;
            console.log('Connected with ID:', this.connectionId);
            resolve();
          }
        } catch (error) {
          console.error('Failed to parse SSE message:', error);
        }
      };

      this.eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        reject(error);
      };

      // 连接超时
      setTimeout(() => {
        if (!this.connectionId) {
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });
  }

  private handleSSEMessage(message: any) {
    console.log('Received SSE message:', message.type);

    switch (message.type) {
      case 'connected':
        this.emit('connected', message.data);
        break;

      case 'heartbeat':
        this.emit('heartbeat', message.data);
        break;

      case 'progress':
        // 进度更新 - 只有 SSE 模式才有
        const progressData = message.data;
        const pendingRequest = this.pendingRequests.get(progressData.requestId);
        if (pendingRequest && pendingRequest.onProgress) {
          pendingRequest.onProgress(progressData);
        }
        this.emit('progress', progressData);
        break;

      case 'mcp-response':
        // 最终响应
        const response = message.data;
        const request = this.pendingRequests.get(response.id);
        if (request) {
          this.pendingRequests.delete(response.id);
          if (response.error) {
            request.reject(new Error(response.error.message));
          } else {
            request.resolve(response.result);
          }
        }
        break;

      case 'broadcast':
        // 广播消息 - 只有 SSE 模式才有
        this.emit('broadcast', message.data);
        break;
    }
  }

  // 支持进度回调的异步调用
  async callTool(
    name: string, 
    args: any,
    onProgress?: (progress: any) => void
  ): Promise<any> {
    if (!this.connectionId) {
      throw new Error('Not connected');
    }

    const requestId = this.generateRequestId();
    const request = {
      id: requestId,
      method: 'tools/call',
      params: { name, arguments: args }
    };

    return new Promise((resolve, reject) => {
      // 注册待处理请求
      this.pendingRequests.set(requestId, { resolve, reject, onProgress });

      // 发送 HTTP 请求
      fetch(`${this.baseUrl}/api/mcp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Connection-ID': this.connectionId!
        },
        body: JSON.stringify(request)
      }).then(response => {
        if (!response.ok) {
          this.pendingRequests.delete(requestId);
          reject(new Error(`HTTP ${response.status}: ${response.statusText}`));
        }
        // HTTP 响应只是确认，真正结果通过 SSE 返回
      }).catch(error => {
        this.pendingRequests.delete(requestId);
        reject(error);
      });

      // 超时处理
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('Request timeout'));
        }
      }, 60000);
    });
  }

  // 支持实时更新的工具列表
  async getTools(): Promise<any[]> {
    return this.sendMCPRequest('tools/list');
  }

  private async sendMCPRequest(method: string, params?: any): Promise<any> {
    if (!this.connectionId) {
      throw new Error('Not connected');
    }

    const requestId = this.generateRequestId();
    const request = { id: requestId, method, params };

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(requestId, { resolve, reject });

      fetch(`${this.baseUrl}/api/mcp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Connection-ID': this.connectionId!
        },
        body: JSON.stringify(request)
      }).then(response => {
        if (!response.ok) {
          this.pendingRequests.delete(requestId);
          reject(new Error(`HTTP ${response.status}: ${response.statusText}`));
        }
      }).catch(error => {
        this.pendingRequests.delete(requestId);
        reject(error);
      });

      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('Request timeout'));
        }
      }, 30000);
    });
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.connectionId = null;
    this.pendingRequests.clear();
  }
}
```

---

## 使用示例对比

### 纯 HTTP 使用方式

```typescript
// 简单直接，但功能有限
const client = new PureHTTPClient('http://localhost:3000');

try {
  // 同步调用，等待结果
  const result = await client.callTool('calculate', {
    operation: 'add',
    a: 5,
    b: 3
  });
  
  console.log('计算结果:', result);

  // 获取工具列表
  const tools = await client.getTools();
  console.log('可用工具:', tools);

} catch (error) {
  console.error('调用失败:', error);
}
```

### HTTP + SSE 使用方式

```typescript
// 功能丰富，支持实时交互
const client = new HTTPSSEClient('http://localhost:3000', 'user123');

// 监听事件
client.on('connected', (data) => {
  console.log('已连接到服务器:', data);
});

client.on('progress', (progress) => {
  console.log(`进度更新: ${progress.progress * 100}% - ${progress.message}`);
});

client.on('broadcast', (data) => {
  console.log('收到广播消息:', data);
});

try {
  // 建立连接
  await client.connect();

  // 支持进度回调的调用
  const result = await client.callTool('slow_calculation', 
    { seconds: 5 },
    (progress) => {
      console.log(`工具执行进度: ${progress.progress * 100}%`);
    }
  );

  console.log('计算结果:', result);

  // 获取工具列表
  const tools = await client.getTools();
  console.log('可用工具:', tools);

} catch (error) {
  console.error('调用失败:', error);
} finally {
  await client.disconnect();
}
```

---

## 性能和资源对比

### 资源消耗

| 指标 | 纯 HTTP | HTTP + SSE |
|------|---------|------------|
| **内存使用** | 低 | 中等（需要维护连接） |
| **CPU 使用** | 低 | 中等（事件处理） |
| **网络连接** | 短暂 | 持久 |
| **服务器负载** | 每请求一次 | 连接建立时较高 |

### 并发处理能力

```typescript
// 纯 HTTP - 处理能力
// 每个请求独立，易于横向扩展
// 适合无状态的 RESTful API

// HTTP + SSE - 处理能力  
// 需要管理连接状态，但支持更丰富的交互
// 单实例连接数有限，但可通过负载均衡扩展
```

### 适用场景

**选择纯 HTTP 模式：**
- ✅ 简单的工具调用
- ✅ 无需实时交互
- ✅ 追求最大并发
- ✅ 无状态服务
- ✅ 简单部署

**选择 HTTP + SSE 模式：**
- ✅ 需要进度反馈
- ✅ 长时间运行的任务
- ✅ 实时通知和推送
- ✅ 复杂的交互流程
- ✅ 更好的用户体验

---

## 总结

### 技术复杂度
- **纯 HTTP**：简单直接，易于理解和维护
- **HTTP + SSE**：复杂一些，但提供更丰富的功能

### 用户体验  
- **纯 HTTP**：传统的请求-响应模式
- **HTTP + SSE**：现代的实时交互体验

### 商业价值
- **纯 HTTP**：适合快速原型和简单服务
- **HTTP + SSE**：适合产品化和高端服务

根据您的需求，如果追求简单快速，选择纯 HTTP；如果要提供更好的用户体验和更丰富的功能，选择 HTTP + SSE。

---

*最后更新：2025年9月26日*