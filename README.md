# Image_manageSys

基于 **AI 视觉大模型（Qwen3-VL）** 的企业素材库系统（轻量 MVP）项目骨架。

当前状态：后端对接端点已完成（认证、素材、版本、标签、分组、分享、审计、图像关键词分析、文本检索），当前主要工作为前端从 mock 切换到真实 API。

## 目录结构

```text
backend/                # 后端（FastAPI）骨架
frontend/               # 前端（Vue 3）骨架
data/                   # 本地运行数据（sqlite/uploads/faiss/logs）
model/                  # 模型与缓存目录
deploy/compose/         # 部署编排目录
docs/                   # 项目文档
scripts/                # 脚本目录
```

## 文档入口

详见 `docs/` 目录。

## 规划中的轻量技术栈

- 前端：Vue 3 + TypeScript
- 后端：FastAPI（Python）
- 元数据：SQLite（后续可迁移 PostgreSQL）
- 文件存储：本地磁盘（后续可迁移 MinIO）
- 检索策略：提示词向量召回（Qdrant）
- 模型：Qwen3-VL（Bailian）
- 部署：Docker Compose

## 后端本地启动（Windows PowerShell）

### 1. 进入后端目录并创建虚拟环境

```powershell
Set-Location D:\myfiles\code\c\CLIP-Image_manageSys\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "."
```

### 2. 启动开发服务

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 验证运行状态

- 健康检查：`http://127.0.0.1:8000/healthz`
- API v1 健康检查：`http://127.0.0.1:8000/api/v1/health`
- Swagger 文档：`http://127.0.0.1:8000/docs`

### 4. 运行后端测试

```powershell
Set-Location D:\myfiles\code\c\CLIP-Image_manageSys\backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
python -m pytest tests -q
```

## API

运行时访问 Swagger：`http://127.0.0.1:8000/docs`，接口详见 `docs/api.md`。

