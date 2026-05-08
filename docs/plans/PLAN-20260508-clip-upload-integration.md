# PLAN-20260508-clip-upload-integration

## 1. 任务背景

素材上传已可用，但上传后尚未触发 Chinese-CLIP 编码流程，前端的 CLIP 分析调用也缺少真实后端接口。

## 2. 目标与验收结果

- 目标 1：上传后自动触发 CLIP 分析并持久化结果。
- 目标 2：提供独立 CLIP 分析接口给前端上传页调用。
- 目标 3：提供模型启动状态可观测能力，便于排障。

验收标准（必须可验证）：
- [x] `POST /api/v1/assets/upload` 返回包含 `clip_analysis` 字段
- [x] `GET /api/v1/clip/status` 可返回模型服务状态
- [x] `POST /api/v1/clip/analyze` 可返回分析结果
- [x] 分析结果持久化（`asset_clip_analysis` 表）
- [x] 后端测试通过

## 3. 本次范围 / 非范围

### 3.1 In Scope
- CLIP 服务初始化与推理封装
- 上传链路接入与失败策略
- CLIP 结果存储与 API 返回

### 3.2 Out of Scope
- 文本检索接口（`/api/v1/search/text`）
- FAISS 向量索引与召回链路

## 4. 技术方案

- 新增 `ClipService`：
  - 默认 provider：`chinese_clip`
  - 测试 provider：`mock`
- 新增表 `asset_clip_analysis` 持久化分析状态与结果
- 上传时同步执行分析，按 `CLIP_REQUIRED_ON_UPLOAD` 控制是否强一致失败
- 增加 `clip` 路由：`/status`、`/analyze`

## 5. 任务拆解与推进顺序

1. 数据结构：表结构 + repository
2. 服务层：模型加载、状态、推理
3. 接口层：上传接入 + 新增 clip endpoint
4. 测试与文档更新

## 6. 风险与回滚

- 风险点：模型依赖未安装导致服务未就绪
- 监控点：`/api/v1/clip/status` 的 `ready/last_error`
- 回滚方案：按文件回滚 clip endpoint/service/schema

## 7. 验证方案

- `python -m pytest backend/tests -q`
- 手工：上传图片后检查响应 `clip_analysis.status`
- 手工：调用 `/api/v1/clip/status` 验证模型状态

## 8. 交付清单

- 代码文件：`assets.py`、`clip.py`、`clip_service.py`、`clip_repository.py`、`database.py`
- 文档文件：`README.md`、`docs/前后端对接-待确认问题.md`
- 依赖文件：`backend/requirements-clip.txt`
