# CLIP-Image_manageSys MVP PRD & 实现规范

> 版本：v0.2.0-draft | 更新：2026-05-07

---

## 1. 当前状态基线

### 已完成（v0.1.0）

| 层级 | 内容 | 状态 |
|------|------|------|
| 后端 core | config / database(SQLite) / security / middleware / exceptions / logging | ✅ 完成 |
| 后端 auth | POST register / POST login / GET me（含 7 个测试） | ✅ 完成 |
| 数据库 | `users` 表（id, username, password_hash, created_at） | ✅ 完成 |
| 前端骨架 | Vue 3 + TS + Vite + Element Plus + Pinia + Vue Router | ✅ 完成 |
| 前端视图 | 8 个页面（素材库/分组/搜索/上传/CLIP说明/审计/登录/详情） | ✅ 完成（模拟数据） |
| 原型验证 | `prototype/index.html` 全流程验证 | ✅ 完成 |

### 待建

| 层级 | 内容 |
|------|------|
| 后端 | assets / tags / collections / versions / share / audit / search 全部 CRUD 端点 |
| 数据库 | 9 张业务表（assets, asset_versions, tags, asset_tags, collections, collection_assets, share_links, asset_embeddings, audit_logs）+ search_logs |
| 后端 schemas | Pydantic 请求/响应模型（抽离到 schemas/） |
| 后端 services | 业务逻辑层（抽离到 services/） |
| 后端 models | ORM 模型（可选，MVP 阶段可用 raw SQL） |
| CLIP 集成 | Chinese-CLIP 模型加载、图像编码、文本编码、FAISS 索引 |
| 前端 API 对接 | 替换模拟数据为真实 API 调用 |
| 部署 | Docker Compose 编排 |

---

## 2. 数据库表设计

### 新增表（按依赖顺序）

```sql
-- 1. 素材主表
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    source TEXT DEFAULT '',
    author_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2. 素材版本
CREATE TABLE asset_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    version_tag TEXT NOT NULL,           -- e.g. "v1.0", "v2.1"
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    note TEXT DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 3. 标签表
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 4. 素材-标签关联
CREATE TABLE asset_tags (
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (asset_id, tag_id)
);

-- 5. 分组（集合）
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 6. 分组-素材关联
CREATE TABLE collection_assets (
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    added_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (collection_id, asset_id)
);

-- 7. 分享链接
CREATE TABLE share_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    expires_at TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 8. 向量嵌入（CLIP）
CREATE TABLE asset_embeddings (
    asset_id INTEGER PRIMARY KEY REFERENCES assets(id) ON DELETE CASCADE,
    version_id INTEGER REFERENCES asset_versions(id),
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    embedding BLOB NOT NULL,             -- 512维 float32 序列化
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 9. 审计日志
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,                -- upload / download / delete / share / edit / view
    target_type TEXT NOT NULL,           -- asset / collection / share_link
    target_id INTEGER,
    detail TEXT DEFAULT '',
    ip_address TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 10. 检索日志（可选 P1）
CREATE TABLE search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    query_text TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    duration_ms REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 3. API 规范（完整清单）

所有接口前缀：`/api/v1`

### 3.1 素材管理（P0）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `POST` | `/assets/upload` | 上传图片（multipart） | editor+ |
| `GET` | `/assets` | 素材列表（分页/标签筛选/搜索） | 公开 |
| `GET` | `/assets/{id}` | 素材详情 | 公开 |
| `PUT` | `/assets/{id}` | 编辑元数据 | editor+ |
| `DELETE` | `/assets/{id}` | 删除素材 | admin |
| `POST` | `/assets/{id}/versions` | 上传新版本 | editor+ |
| `GET` | `/assets/{id}/versions` | 获取版本历史 | 公开 |

#### `GET /api/v1/assets` 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 10，最大 50 |
| `tags` | string | 否 | 逗号分隔的标签名，AND 关系 |
| `q` | string | 否 | 全局搜索（名称+描述模糊匹配） |
| `sort` | string | 否 | date_desc / date_asc / name，默认 date_desc |

#### `GET /api/v1/assets` 响应

```json
{
  "items": [ { "id":1, "name":"...", "description":"...", "tags":["..."], ... } ],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

#### `POST /api/v1/assets/upload` 请求

- Content-Type: `multipart/form-data`
- 字段：`file`(必填), `name`, `description`, `tags`(逗号分隔), `source`
- file 限制：JPG/PNG/WebP，≤20MB

#### `POST /api/v1/assets/upload` 响应（201）

```json
{
  "id": 22,
  "name": "...", "description": "...", "tags": [...],
  "file_size": 2410112, "mime_type": "image/png",
  "versions": [{"version_tag": "v1.0", ...}],
  "clip_embedding": { "model": "chinese-clip-vit-b-16", "indexed": true }
}
```

#### 错误码

| 状态码 | code | 说明 |
|--------|------|------|
| 400 | `FILE_TOO_LARGE` | 文件超过 20MB |
| 400 | `UNSUPPORTED_FORMAT` | 不支持的格式 |
| 404 | `ASSET_NOT_FOUND` | 素材不存在 |
| 403 | `FORBIDDEN` | 权限不足 |

### 3.2 标签管理（P0）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/tags` | 标签列表 | 公开 |
| `POST` | `/tags` | 创建标签 | editor+ |
| `DELETE` | `/tags/{id}` | 删除标签 | admin |

#### `GET /api/v1/tags` 响应

```json
{
  "items": [
    { "id": 1, "name": "科技感", "asset_count": 12 },
    { "id": 2, "name": "产品图", "asset_count": 8 }
  ]
}
```

### 3.3 分组管理（P0）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/collections` | 分组列表 | 公开 |
| `POST` | `/collections` | 创建分组 | editor+ |
| `GET` | `/collections/{id}` | 分组详情（含素材列表） | 公开 |
| `PUT` | `/collections/{id}` | 编辑分组信息 | editor+ |
| `DELETE` | `/collections/{id}` | 删除分组 | admin |
| `POST` | `/collections/{id}/assets` | 向分组添加素材 | editor+ |
| `DELETE` | `/collections/{id}/assets/{asset_id}` | 从分组移除素材 | editor+ |

### 3.4 分享链接（P0）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `POST` | `/share-links` | 创建分享链接 | editor+ |
| `GET` | `/share-links/{token}` | 访问分享的素材 | 公开（token验证） |
| `DELETE` | `/share-links/{id}` | 撤销分享链接 | editor+ |

#### `POST /api/v1/share-links` 请求

```json
{ "asset_id": 1, "expires_in_hours": 24 }
```

#### `POST /api/v1/share-links` 响应

```json
{
  "id": 1,
  "token": "abc123def456",
  "url": "https://xxx/share/abc123def456",
  "expires_at": "2026-05-08T14:32:10"
}
```

### 3.5 审计日志（P0）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/audit-logs` | 审计日志列表（可按用户/操作/时间筛选） | admin |

### 3.6 语义搜索（P1）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `POST` | `/search/text` | 文本搜图（Chinese-CLIP） | 公开 |
| `POST` | `/search/image` | 图搜图（Chinese-CLIP） | 公开 |

#### `POST /api/v1/search/text` 请求

```json
{ "query": "蓝色科技感背景图", "page": 1, "page_size": 10 }
```

#### `POST /api/v1/search/text` 响应

```json
{
  "items": [
    {
      "asset": { "id":1, "name":"科技感蓝色背景图", "thumb":"...", "tags":[...] },
      "score": 0.92
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 10
}
```

---

## 4. 后端目录结构（目标态）

```
backend/app/
├── main.py
├── core/
│   ├── config.py          ✅ 完成
│   ├── database.py        （需扩展：加所有建表 DDL）
│   ├── exceptions.py      ✅ 完成
│   ├── logging.py         ✅ 完成
│   ├── middleware.py       ✅ 完成
│   └── security.py        ✅ 完成（需扩展：加角色字段到 users 表）
├── models/                【待建：可选，MVP 阶段用 raw SQL + repositories】
├── schemas/               【待建：Pydantic 模型】
│   ├── asset.py
│   ├── tag.py
│   ├── collection.py
│   ├── share_link.py
│   ├── search.py
│   └── audit.py
├── api/v1/
│   ├── router.py          ✅ 完成（需扩展：加新路由模块）
│   └── endpoints/
│       ├── auth.py        ✅ 完成
│       ├── health.py      ✅ 完成
│       ├── assets.py      【待建】
│       ├── tags.py        【待建】
│       ├── collections.py 【待建】
│       ├── share.py       【待建】
│       ├── audit.py       【待建】
│       └── search.py      【待建 P1】
├── services/              【待建：业务逻辑】
│   ├── asset_service.py
│   ├── search_service.py  （P1）
│   └── clip_service.py    （P1）
├── repositories/          （已有 user_repository，扩展模式）
│   ├── asset_repository.py
│   ├── tag_repository.py
│   ├── collection_repository.py
│   ├── share_repository.py
│   └── audit_repository.py
└── tasks/                 【待建 P2】
```

---

## 5. 开发计划（分里程碑）

### 里程碑 1：P0 素材管理闭环（预计最先做）

**目标**：上传 + 查看 + 编辑 + 删除素材的完整后端链路

**后端任务**：
1. 扩展 `database.py`：建 assets / asset_versions / tags / asset_tags 表
2. 写 `schemas/asset.py`、`schemas/tag.py`
3. 写 `repositories/asset_repository.py`、`repositories/tag_repository.py`
4. 写 `services/asset_service.py`（文件存储、缩略图生成）
5. 写 `endpoints/assets.py`、`endpoints/tags.py`
6. 注册路由到 `api/v1/router.py`
7. 写测试：`tests/test_assets.py`（上传/列表/详情/编辑/删除/版本）

**前端任务**：
1. AssetsView / AssetDetailView / UploadView 接入真实 API（替换模拟数据）
2. 对接分页参数

**验收标准**：
- [ ] `POST /api/v1/assets/upload` 上传一张图 → 201，文件落盘，DB 写入
- [ ] `GET /api/v1/assets?page=1&page_size=10` → 返回 10 条，分页正确
- [ ] `GET /api/v1/assets?tags=科技感` → 仅返回含该标签的素材
- [ ] `PUT /api/v1/assets/{id}` → 更新 name/description/tags 成功
- [ ] `DELETE /api/v1/assets/{id}` → admin 成功，editor 403
- [ ] `POST /api/v1/assets/{id}/versions` → 上传新版本成功，版本链可查
- [ ] 前端素材库页面从 API 加载数据，分页组件工作正常

### 里程碑 2：P0 分组与分享（第二批）

**目标**：分组管理 + 受控分享链接

**后端任务**：
1. 建 collections / collection_assets / share_links 表
2. 写对应 schemas / repositories / services / endpoints
3. 写测试

**验收标准**：
- [ ] 创建分组 → 添加素材到分组 → 查看分组内素材
- [ ] 创建分享链接 → 通过 token 访问素材 → 过期 token 403
- [ ] 撤销分享链接 → token 失效

### 里程碑 3：P0 审计 + 角色完善（第三批）

**目标**：审计日志自动记录 + 角色权限精确控制

**任务**：
1. users 表加 `role` 字段（admin/editor/guest）
2. 建 audit_logs 表 + 自动记录中间件
3. GET /audit-logs 端点（admin only）
4. 各端点加角色校验

**验收标准**：
- [ ] 上传/下载/删除操作自动写入 audit_logs
- [ ] GET /audit-logs 可按用户/操作/时间筛选
- [ ] 访客只能读，编辑能上传编辑，管理员全权限

### 里程碑 4：P1 Chinese-CLIP 检索（第四批）

**目标**：文本搜图 + 图搜图

**任务**：
1. 集成 Chinese-CLIP 模型（CN-CLIP ViT-B/16）
2. 上传时同步提取图像向量 → 写入 asset_embeddings + FAISS
3. 实现文本编码 + FAISS 相似度检索
4. POST /search/text 端点
5. POST /search/image 端点（可选：先做以文搜图）

**验收标准**：
- [ ] 上传图片后自动生成 512 维向量
- [ ] 搜"蓝色科技背景"返回相关结果，不依赖标签精确匹配
- [ ] 搜索结果按余弦相似度降序排列
- [ ] 搜索响应时间 < 2s（10万规模内）

---

## 6. 开发约定（重申）

- **分支**：`feature/<module>-<desc>` → PR → `dev` → milestone → `main`
- **提交**：`feat(module): what` / `fix(module): what`
- **P0 优先**：先完成所有管理功能，再接入 CLIP
- **每步有测试**：新端点必须配测试（参照 `test_app_baseline.py` 风格）
- **API 版本化**：所有新端点统一在 `/api/v1/` 下
- **不在首期引入**：Celery、Redis、PostgreSQL、MinIO、视频检索

---

## 7. 验收标准总清单

### P0 闭环验收

- [ ] 用户注册/登录/JWT 认证
- [ ] 素材上传（多格式 + 大小校验 + 自动缩略图）
- [ ] 素材列表（分页 10 条 + 标签筛选 + 关键词搜索）
- [ ] 素材详情 + 元数据编辑
- [ ] 素材删除（admin only + 审计记录）
- [ ] 素材版本链（上传新版本 + 查看历史）
- [ ] 标签 CRUD + 素材打标
- [ ] 分组 CRUD + 素材移入/移出
- [ ] 分享链接（创建/访问/过期/撤销）
- [ ] 审计日志（自动记录 + 后台查询）
- [ ] 角色权限（admin/editor/guest 三层）

### P1 闭环验收

- [ ] 文本搜图（自然语言 → 向量检索 → 排序结果）
- [ ] 上传自动向量化（Chinese-CLIP 编码 → FAISS 索引）
- [ ] 搜索结果可复现（同一查询返回相同结果）
- [ ] 搜索日志统计
