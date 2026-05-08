# CLIP-Image_manageSys

基于 **Chinese-CLIP** 的企业素材库系统（轻量 MVP）项目骨架。

当前状态：后端对接端点已完成（认证、素材、版本、标签、分组、分享、审计、CLIP 分析、文本检索），当前主要工作为前端从 mock 切换到真实 API。

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

- `docs/begin.md`
- `docs/开发起步文档.md`
- `docs/开发注意事项.md`
- `docs/后端开发任务推进规范.md`
- `docs/Git版本规划与前后端提交流程.md`
- `docs/plans/PLAN-TEMPLATE.md`
- `docs/plans/PLAN-20260507-git-version-planning.md`
- `docs/plans/PLAN-20260507-rbac-m1.md`
- `docs/plans/PLAN-20260507-assets-crud-m2.md`
- `docs/plans/PLAN-20260507-p0-api-completion.md`
- `docs/plans/PLAN-20260508-clip-upload-integration.md`
- `docs/plans/PLAN-20260508-search-text-p1.md`

## 规划中的轻量技术栈

- 前端：Vue 3 + TypeScript
- 后端：FastAPI（Python）
- 元数据：SQLite（后续可迁移 PostgreSQL）
- 文件存储：本地磁盘（后续可迁移 MinIO）
- 向量检索：FAISS
- 模型：Chinese-CLIP
- 部署：Docker Compose

## 后端本地启动（Windows PowerShell）

### 1. 进入后端目录并创建虚拟环境

```powershell
Set-Location D:\myfiles\code\c\CLIP-Image_manageSys\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-clip.txt
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

## 认证接口快速验证（注册 / 登录 / 判断是否登录成功）

### 1. 注册账号

```powershell
$registerBody = @{
  username = "demo_user"
  password = "Passw0rd!"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/auth/register" `
  -ContentType "application/json" `
  -Body $registerBody
```

### 2. 登录获取 token

```powershell
$loginBody = @{
  username = "demo_user"
  password = "Passw0rd!"
} | ConvertTo-Json

$loginResp = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/auth/login" `
  -ContentType "application/json" `
  -Body $loginBody

$token = $loginResp.access_token
```

### 3. 判断登录是否成功（调用 `/auth/me`）

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/api/v1/auth/me" `
  -Headers @{ Authorization = "Bearer $token" }
```

当 `/api/v1/auth/me` 返回 `200` 且包含当前用户信息时，可判定登录成功。

### 4. 管理员接口验证（`/auth/users`）

系统默认规则：**首个注册用户为 `admin`，后续注册用户为 `editor`**。

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/api/v1/auth/users" `
  -Headers @{ Authorization = "Bearer $token" }
```

当 token 对应 `admin` 角色时返回用户列表；非 admin 返回 `403`。

## 素材接口（M2 已实现）

- `POST /api/v1/assets/upload`（需登录，admin/editor）
  - 支持：`JPG/PNG/WebP`
  - 大小限制：`<=20MB`
  - 上传后自动执行 CLIP 分析（失败时在响应 `clip_analysis` 返回失败原因）
- `GET /api/v1/assets?page=1&page_size=10&query=...`（访客可读）
- `GET /api/v1/assets/{id}`（访客可读）
- `PUT /api/v1/assets/{id}`（admin 可改全部，editor 仅可改自己上传）
- `DELETE /api/v1/assets/{id}`（admin 可删全部，editor 仅可删自己上传）
- `GET /api/v1/assets/{id}/download`（需登录，guest 禁止）
- `POST /api/v1/assets/{id}/versions`（需登录，admin/editor）
- `GET /api/v1/assets/{id}/versions`（访客可读）

## 其他 P0 对接接口（已实现）

- 标签：`GET/POST/DELETE /api/v1/tags`
- 分组：`GET/POST /api/v1/collections`、`GET/PUT/DELETE /api/v1/collections/{id}`、`POST /api/v1/collections/{id}/assets`、`DELETE /api/v1/collections/{id}/assets/{asset_id}`
- 分享：`GET/POST/DELETE /api/v1/share-links`
- 审计：`GET /api/v1/audit-logs`（admin）

## CLIP 分析接口（已实现）

- `GET /api/v1/clip/status`：查看模型服务状态（enabled/provider/ready/last_error）
- `POST /api/v1/clip/analyze`：上传图片执行 CLIP 分析（需登录，admin/editor）

## 语义检索接口（已实现）

- `POST /api/v1/search/text`：文本搜图，请求 `{ query, page, page_size }`
- 响应：`{ items: [{ asset, score }], total, page, page_size }`

可配置环境变量：

- `CLIP_ENABLED`：是否启用 CLIP（默认 `true`）
- `CLIP_PROVIDER`：`chinese_clip` 或 `mock`（默认 `chinese_clip`）
- `CLIP_MODEL_NAME`：默认 `OFA-Sys/chinese-clip-vit-base-patch16`
- `CLIP_MODEL_REVISION`：默认 `main`
- `CLIP_DEVICE`：默认 `cpu`
- `CLIP_REQUIRED_ON_UPLOAD`：上传时是否强制 CLIP 成功（默认 `false`）

