# 使用GitHub Packages实现私有MCP核心 + 公开包装器

## 架构概述

```
私有包 (@your-username/mcp-core)     ←→     公开MCP服务器 (your-mcp-server)
├── 核心业务逻辑                           ├── MCP协议实现
├── 数据处理算法                           ├── 接口适配层  
├── API调用逻辑                           ├── 配置管理
└── 关键功能                             └── 使用私有包
```

## 步骤1：创建私有核心包

### 1.1 创建私有仓库结构
```bash
mkdir mcp-core-private
cd mcp-core-private
npm init -y
```

### 1.2 配置 package.json
```json
{
  "name": "@your-username/mcp-core",
  "version": "1.0.0",
  "private": false,
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "prepublishOnly": "npm run build"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/your-username/mcp-core-private.git"
  },
  "publishConfig": {
    "registry": "https://npm.pkg.github.com"
  }
}
```

### 1.3 创建核心代码
```typescript
// src/index.ts - 私有核心逻辑
export interface StockData {
  symbol: string;
  price: number;
  analysis: string;
}

export class StockAnalyzer {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  // 核心算法 - 保密
  async analyzeStock(symbol: string): Promise<StockData> {
    // 复杂的分析算法
    const data = await this.fetchStockData(symbol);
    const analysis = this.performAdvancedAnalysis(data);
    
    return {
      symbol,
      price: data.price,
      analysis: analysis
    };
  }

  private async fetchStockData(symbol: string) {
    // 私有API调用逻辑
    // 使用专有数据源和算法
  }

  private performAdvancedAnalysis(data: any): string {
    // 核心分析算法 - 商业机密
    return "Advanced analysis result";
  }
}

export class DataProcessor {
  // 其他核心功能
  processFinancialData(data: any) {
    // 专有数据处理逻辑
  }
}
```

### 1.4 GitHub Actions发布配置
```yaml
# .github/workflows/publish.yml
name: Publish Private Package

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          registry-url: 'https://npm.pkg.github.com'
      - run: npm ci
      - run: npm run build
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 步骤2：创建公开MCP服务器

### 2.1 创建公开仓库
```bash
mkdir awesome-stock-mcp
cd awesome-stock-mcp
npm init -y
```

### 2.2 配置 package.json
```json
{
  "name": "awesome-stock-mcp",
  "version": "1.0.0",
  "description": "MCP Server for Stock Analysis",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@your-username/mcp-core": "^1.0.0",
    "@modelcontextprotocol/sdk": "latest"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/your-username/awesome-stock-mcp.git"
  }
}
```

### 2.3 创建 .gitignore（重要！）
```
# 敏感文件 - 绝对不提交
.npmrc
.env
.encrypted-config
config/secrets.json
*.key
*.pem

# 构建和依赖
node_modules/
dist/
.DS_Store
```

### 2.4 创建MCP服务器代码
```typescript
// src/index.ts - 公开的MCP适配器
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StockAnalyzer, DataProcessor } from '@your-username/mcp-core';

class StockMcpServer {
  private server: Server;
  private analyzer: StockAnalyzer;
  private processor: DataProcessor;

  constructor() {
    this.server = new Server(
      { name: 'stock-analysis-server', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );
    
    // 使用私有包的功能
    this.analyzer = new StockAnalyzer(process.env.API_KEY!);
    this.processor = new DataProcessor();
    
    this.setupTools();
  }

  private setupTools() {
    // 只暴露MCP接口，隐藏实现细节
    this.server.setRequestHandler(
      'tools/list',
      async () => ({
        tools: [
          {
            name: 'analyze_stock',
            description: 'Analyze stock performance',
            inputSchema: {
              type: 'object',
              properties: {
                symbol: { type: 'string' }
              }
            }
          }
        ]
      })
    );

    this.server.setRequestHandler(
      'tools/call',
      async (request) => {
        const { name, arguments: args } = request.params;

        if (name === 'analyze_stock') {
          // 调用私有包的功能
          const result = await this.analyzer.analyzeStock(args.symbol);
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(result, null, 2)
              }
            ]
          };
        }

        throw new Error(`Unknown tool: ${name}`);
      }
    );
  }

  async start() {
    await this.server.connect(process.stdout, process.stdin);
  }
}

// 启动服务器
const server = new StockMcpServer();
server.start().catch(console.error);
```

### 2.5 README.md 示例
```markdown
# Awesome Stock MCP Server

一个强大的股票分析MCP服务器，提供专业级的股票数据分析功能。

## 功能特点
- 🚀 高性能股票分析
- 📊 专业级数据处理
- 🔒 企业级安全性
- 📈 实时市场数据

## 安装使用

\`\`\`bash
# 需要GitHub Token访问私有依赖
npm install awesome-stock-mcp
\`\`\`

## 配置

创建 `.env` 文件：
\`\`\`
API_KEY=your_api_key
GITHUB_TOKEN=your_github_token
\`\`\`

## Claude配置

\`\`\`json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "node",
      "args": ["path/to/awesome-stock-mcp/dist/index.js"]
    }
  }
}
\`\`\`

## 贡献

欢迎提交Issue和PR！核心分析功能由专有算法驱动。
```

## 步骤3：隐藏私有包访问密钥 🔐

### 方案一：环境变量（推荐）

#### 3.1 修改 .npmrc（不提交到git）
```bash
# .npmrc - 添加到 .gitignore
@your-username:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```

#### 3.2 用户配置说明
```markdown
# 在README中说明用户如何配置

## 安装前置条件

1. 联系作者获取私有包访问权限
2. 创建 `.npmrc` 文件：

\`\`\`
@your-username:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=YOUR_GITHUB_TOKEN
\`\`\`

3. 设置环境变量：
\`\`\`bash
export GITHUB_TOKEN=your_github_token
\`\`\`
```

### 方案二：运行时动态获取

#### 3.3 创建密钥管理器
```typescript
// src/auth/keyManager.ts
export class KeyManager {
  private static instance: KeyManager;
  private githubToken?: string;

  static getInstance(): KeyManager {
    if (!KeyManager.instance) {
      KeyManager.instance = new KeyManager();
    }
    return KeyManager.instance;
  }

  async initializeKey(): Promise<string> {
    // 方式1: 从环境变量读取
    if (process.env.GITHUB_TOKEN) {
      this.githubToken = process.env.GITHUB_TOKEN;
      return this.githubToken;
    }

    // 方式2: 从用户输入获取
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    return new Promise((resolve) => {
      rl.question('请输入GitHub Token (私有包访问): ', (token) => {
        this.githubToken = token;
        rl.close();
        resolve(token);
      });
    });
  }

  getToken(): string {
    if (!this.githubToken) {
      throw new Error('GitHub Token 未初始化，请先调用 initializeKey()');
    }
    return this.githubToken;
  }
}
```

### 方案三：加密配置文件

#### 3.4 创建配置加密工具
```typescript
// src/config/encryptedConfig.ts
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

export class EncryptedConfig {
  private static readonly CONFIG_FILE = '.encrypted-config';
  private static readonly ALGORITHM = 'aes-256-gcm';

  static encryptConfig(data: any, password: string): void {
    const key = crypto.scryptSync(password, 'salt', 32);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher(this.ALGORITHM, key);
    
    let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    fs.writeFileSync(this.CONFIG_FILE, JSON.stringify({
      encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    }));
  }

  static decryptConfig(password: string): any {
    if (!fs.existsSync(this.CONFIG_FILE)) {
      throw new Error('配置文件不存在');
    }

    const configData = JSON.parse(fs.readFileSync(this.CONFIG_FILE, 'utf8'));
    const key = crypto.scryptSync(password, 'salt', 32);
    
    const decipher = crypto.createDecipher(this.ALGORITHM, key);
    decipher.setAuthTag(Buffer.from(configData.authTag, 'hex'));
    
    let decrypted = decipher.update(configData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return JSON.parse(decrypted);
  }
}
```

### 方案四：动态包安装

#### 3.5 修改MCP服务器启动逻辑
```typescript
// src/index.ts - 智能启动
import { KeyManager } from './auth/keyManager';
import { execSync } from 'child_process';

class StockMcpServer {
  private analyzer?: any;
  private processor?: any;

  async initialize() {
    try {
      // 尝试直接导入（如果已安装）
      const coreModule = await import('@your-username/mcp-core');
      this.analyzer = new coreModule.StockAnalyzer(process.env.API_KEY!);
      this.processor = new coreModule.DataProcessor();
    } catch (error) {
      console.log('私有包未安装，开始配置...');
      await this.setupPrivatePackage();
      
      // 重新导入
      const coreModule = await import('@your-username/mcp-core');
      this.analyzer = new coreModule.StockAnalyzer(process.env.API_KEY!);
      this.processor = new coreModule.DataProcessor();
    }
  }

  private async setupPrivatePackage() {
    const keyManager = KeyManager.getInstance();
    const token = await keyManager.initializeKey();
    
    // 动态创建 .npmrc
    const npmrcContent = `
@your-username:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${token}
`;
    
    require('fs').writeFileSync('.npmrc', npmrcContent);
    
    console.log('正在安装私有依赖包...');
    try {
      execSync('npm install @your-username/mcp-core', { 
        stdio: 'inherit',
        env: { ...process.env, GITHUB_TOKEN: token }
      });
      console.log('私有包安装成功！');
    } catch (error) {
      throw new Error('私有包安装失败，请检查访问权限');
    }
  }

  // ... 其他方法
}
```

### 方案五：License验证服务

#### 3.6 创建许可证验证
```typescript
// src/license/validator.ts
export class LicenseValidator {
  private static readonly LICENSE_SERVER = 'https://your-license-server.com/api/validate';

  static async validateLicense(licenseKey: string): Promise<boolean> {
    try {
      const response = await fetch(this.LICENSE_SERVER, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ licenseKey })
      });
      
      const result = await response.json();
      return result.valid && result.packageAccess;
    } catch {
      return false;
    }
  }

  static async getPackageToken(licenseKey: string): Promise<string> {
    const response = await fetch(`${this.LICENSE_SERVER}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ licenseKey })
    });
    
    const result = await response.json();
    return result.token;
  }
}
```

### 安全最佳实践

#### .gitignore 配置
```
# 敏感文件 - 绝对不要提交
.npmrc
.env
.encrypted-config
config/secrets.json
*.key
*.pem

# 构建文件
node_modules/
dist/
```

#### 用户安装流程
```markdown
## 安装说明

### 方式1: 环境变量
1. 联系作者获取访问权限
2. 设置环境变量: `GITHUB_TOKEN=your_token`
3. 运行: `npm install && npm start`

### 方式2: 交互式配置
1. 运行: `npm start`
2. 按提示输入GitHub Token
3. 自动安装并启动

### 方式3: 许可证模式
1. 购买许可证获取License Key
2. 运行: `npm start --license YOUR_LICENSE_KEY`
3. 自动验证并配置
```

## 步骤4：设置GitHub Token

### 4.1 创建Personal Access Token
1. 访问 GitHub Settings → Developer settings → Personal access tokens
2. 创建新token，权限包括：
   - `read:packages` 
   - `write:packages`

### 4.2 配置环境变量（用户端）
```bash
# 本地开发
export GITHUB_TOKEN=your_token_here

# 或在用户的 .env 文件中
echo "GITHUB_TOKEN=your_token" >> .env
```

## 步骤5：发布和使用

### 5.1 发布私有包
```bash
cd mcp-core-private
npm run build
npm publish
```

### 5.2 安装到公开项目
```bash
cd awesome-stock-mcp
npm install @your-username/mcp-core
```

### 5.3 发布公开项目
```bash
npm publish  # 发布到公共npm registry
```

## 优势总结

✅ **代码保护**: 核心算法完全私有  
✅ **开源友好**: 公开项目可获得社区贡献  
✅ **商业价值**: 私有包可以授权给付费用户  
✅ **技术展示**: 公开项目展示你的MCP开发能力  
✅ **版本控制**: 独立版本管理，更新灵活  

## 注意事项

1. 私有包使用需要GitHub Token
2. 用户需要有访问私有仓库的权限
3. 可以通过GitHub Team管理访问权限
4. 考虑为企业用户提供不同的访问级别

这样，你就实现了一个完美的"公开展示 + 私有核心"的MCP架构！