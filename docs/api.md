# API 接口

运行时访问 Swagger 文档：`http://127.0.0.1:8000/docs`

## 素材接口

- `POST /api/v1/assets/upload`（需登录，admin/editor）
  - 支持：`JPG/PNG/WebP`
  - 大小限制：`<=20MB`
- 上传后自动执行 Qwen3-VL 图生文分析（生成可复现提示词 + 摘要 + 关键词，失败时在响应 `clip_analysis` 返回失败原因）
- `GET /api/v1/assets?page=1&page_size=10&query=...`（访客可读）
- `GET /api/v1/assets/{id}`（访客可读）
- `PUT /api/v1/assets/{id}`（admin 可改全部，editor 仅可改自己上传）
- `DELETE /api/v1/assets/{id}`（admin 可删全部，editor 仅可删自己上传）
- `GET /api/v1/assets/{id}/download`（需登录，guest 禁止）
- `POST /api/v1/assets/{id}/versions`（需登录，admin/editor）
- `GET /api/v1/assets/{id}/versions`（访客可读）

## 其他 P0 对接接口

- 标签：`GET/POST/DELETE /api/v1/tags`
- 分组：`GET/POST /api/v1/collections`、`GET/PUT/DELETE /api/v1/collections/{id}`、`POST /api/v1/collections/{id}/assets`、`DELETE /api/v1/collections/{id}/assets/{asset_id}`
- 分享：`GET/POST/DELETE /api/v1/share-links`
- 审计：`GET /api/v1/audit-logs`（admin）

## 图像图生文分析接口

- `GET /api/v1/clip/status`：查看模型服务状态（enabled/provider/ready/last_error）
- `POST /api/v1/clip/analyze`：上传图片执行图生文（需登录，admin/editor）
- 返回会包含 `provider`，`qwen3_vl` 表示真实模型，`mock` 只用于本地/测试。
- 返回字段聚焦 `prompt + summary + keywords`，其中 `prompt` 用于后续文生图复现与搜索。

## 提示词向量检索接口

- `POST /api/v1/search/text`：文本搜图，请求 `{ query, page, page_size }`
- 响应：`{ items: [{ asset, score }], total, page, page_size }`
- 当前通过提示词向量召回（Qdrant + Embedding）。

## 可配置环境变量

- `CLIP_ENABLED`：是否启用图片分析（默认 `true`）
- `CLIP_PROVIDER`：`qwen3_vl` 或 `mock`（默认 `qwen3_vl`）
- `CLIP_MODEL_NAME`：默认 `qwen3-vl-plus`
- `CLIP_MODEL_REVISION`：默认 `main`
- `CLIP_REQUIRED_ON_UPLOAD`：上传时是否强制 CLIP 成功（默认 `false`）
- `DASHSCOPE_API_KEY`：Bailian API Key（使用 `qwen3_vl` 必填）
- `QWEN_BASE_URL`：默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `TEXT_EMBEDDING_MODEL`：提示词向量模型，默认 `text-embedding-v4`
- `VECTOR_ENABLED`：是否启用向量检索（默认 `true`）
- `VECTOR_PROVIDER`：当前支持 `qdrant`
- `VECTOR_COLLECTION_NAME`：向量集合名，默认 `asset_prompts`
- `VECTOR_DB_PATH`：Qdrant 本地数据目录，默认 `data/vector_db`
