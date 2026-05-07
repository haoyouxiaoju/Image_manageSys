# CLIP-Image_manageSys

基于 **Chinese-CLIP** 的企业素材库系统（轻量 MVP）项目骨架。

当前状态：已完成后端基础代码基线（`v0.1.0`、`/api/v1`、核心中间件、健康检查、注册/登录/JWT 登录态校验、基础角色权限）。

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

