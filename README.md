# Image_manageSys

基于 **AI 视觉大模型（Qwen3-VL）** 的企业素材库系统。

核心功能：上传图片 → AI 自动生成描述/标签 → 语义向量搜索 + LLM 相关性评分。

## 前置软件

| 软件 | 用途 | 最低版本 |
|------|------|----------|
| Python | 后端运行环境 | 3.12+ |
| Node.js | 前端运行环境 | 18+ |

| Nginx | 反向代理（统一入口） | 1.20+ |
| Git | 版本管理 | 2.0+ |

## 目录结构

```text
backend/                # FastAPI 后端
frontend/               # Vue 3 前端
data/                   # 运行数据（sqlite/uploads/vector_db）
model/                  # 模型缓存目录
deploy/compose/         # Docker Compose 部署编排
docs/                   # 项目文档
scripts/                # 工具脚本
nginx.conf              # Nginx 反向代理配置
```

## 技术栈

- **前端**：Vue 3 + TypeScript + Element Plus
- **后端**：FastAPI（Python）
- **元数据**：SQLite
- **文件存储**：本地磁盘（Nginx 直读）
- **向量检索**：Qdrant（本地模式）+ DashScope text-embedding-v4
- **视觉分析**：Qwen3-VL（Bailian DashScope API）
- **Agent 搜索**：qwen-plus function calling + LLM 相关性评分

## 架构

```
Browser → Nginx(:80) → /           → Vite dev server (:5173)   [前端]
                      → /files/     → data/uploads/ 磁盘直读    [静态文件]
                      → /api/       → FastAPI (:8000)           [后端 API]
                      → /api/agent  → FastAPI (:8000)           [Agent 搜索]
```

## 本地启动

### 1. 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:PYTHONPATH = "."
$env:ASSET_BASE_URL = "http://localhost"

# 启动
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后验证：
- 健康检查：`http://127.0.0.1:8000/healthz`
- Swagger：`http://127.0.0.1:8000/docs`

### 2. 前端

```powershell
cd frontend
npm install
npm run dev
```

Vite 开发服务器默认运行在 `http://localhost:5173`。

### 3. Nginx（统一入口）

```powershell
# 管理员终端
nginx -c ./nginx.conf
```

启动后访问 `http://localhost`（端口 80），全部流量经 Nginx 分发：

| 路径 | 处理方式 |
|------|----------|
| `/` | 代理到 Vite `:5173` |
| `/files/` | Nginx 直读 `data/uploads/` |
| `/api/` | 代理到 FastAPI `:8000` |

停止 Nginx：`nginx -s quit`

### 4. 运行测试

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
python -m pytest tests -q
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ASSET_BASE_URL` | `` | 图片资源基础 URL。本地用 `http://localhost`，服务器部署设为域名，留空则使用相对路径 |
| `DASHSCOPE_API_KEY` | — | Bailian API Key（必填） |
| `VECTOR_ENABLED` | `true` | 是否启用向量检索 |
| `AGENT_ENABLED` | `true` | 是否启用 Agent 搜索 |
| `AGENT_MIN_SCORE` | `0.5` | 搜索结果最低相似度阈值 |
| `AGENT_CHAT_MODEL` | `qwen-plus` | Agent 使用的 LLM 模型 |
| `VISION_REQUIRED_ON_UPLOAD` | `false` | 上传时是否强制 AI 分析成功 |
| `UPLOADS_DIR` | `../data/uploads` | 上传文件存储目录 |
| `VECTOR_DB_PATH` | `../data/vector_db` | Qdrant 数据目录 |

## API

运行时访问 Swagger：`http://127.0.0.1:8000/docs`，接口详见 `docs/api.md`。

## 服务器部署

### 1. 打包前端

```bash
cd frontend
npm run build    # 输出到 dist/
```

### 2. 修改 Nginx 配置

将 `nginx.conf` 中的前端路由从代理 Vite 改为静态文件：

```nginx
# 开发（代理 Vite）
# location / { proxy_pass http://127.0.0.1:5173; ... }

# 生产（静态文件）
location / {
    root D:/myfiles/code/c/CLIP-Image_manageSys/frontend/dist;
    try_files $uri $uri/ /index.html;
}
```

### 3. 设置图片 URL

```bash
export ASSET_BASE_URL="http://你的服务器IP或域名"
```

确保后端设置了这个环境变量，图片的 `file_url` 会使用绝对路径指向 Nginx。

### 4. 启动服务

```bash
# 后端
cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000

# Nginx
nginx -c /path/to/nginx.conf
```

### 5. 开放端口

- 防火墙开放 80 端口
- 如用云服务器，安全组放行 80 端口
- 浏览器访问 `http://服务器IP` 即可

## 文档

详见 `docs/` 目录。
