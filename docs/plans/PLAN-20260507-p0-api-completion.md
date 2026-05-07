# PLAN-20260507-p0-api-completion

## 1. 任务背景

前端已完成主要页面与交互，`docs/前后端对接-待确认问题.md` 中仍有多项 P0 接口未就绪，阻塞全量联调验收。

## 2. 目标与验收结果

- 目标 1：补齐 P0 缺失接口（版本、标签、分组、分享、审计）。
- 目标 2：保持与当前前端调用契约一致。
- 目标 3：更新对接清单状态，形成可验收结果。

验收标准（必须可验证）：
- [x] 版本接口：`POST/GET /api/v1/assets/{id}/versions`
- [x] 标签接口：`GET/POST/DELETE /api/v1/tags`
- [x] 分组接口：`GET/POST/GET{id}/PUT/DELETE /api/v1/collections` + 关系接口
- [x] 分享接口：`GET/POST/DELETE /api/v1/share-links`
- [x] 审计接口：`GET /api/v1/audit-logs`（admin only）
- [x] 后端测试通过
- [x] 对接清单文档状态更新完成

## 3. 本次范围 / 非范围

### 3.1 In Scope
- P0 缺失接口与最小权限控制
- 数据库表已存在前提下的仓储/路由落地

### 3.2 Out of Scope
- P1：`/api/v1/search/text`、`/api/v1/clip/analyze`
- 复杂业务策略（例如分享密码、版本回滚流程）

## 4. 技术方案

- 在 `asset_repository` 扩展版本与标签能力
- 新增 `tag_repository`、`collection_repository`、`share_link_repository`、`audit_repository`
- 新增 endpoint：`tags.py`、`collections.py`、`share_links.py`、`audit_logs.py`
- 统一复用鉴权上下文 `get_current_user`

## 5. 任务拆解与推进顺序

1. 补齐仓储层能力（版本/标签/分组/分享/审计）
2. 落地 API 路由与权限控制
3. 增加测试覆盖
4. 更新对接清单文档

## 6. 风险与回滚

- 风险点：接口字段和前端映射不一致
- 监控点：联调日志与测试失败信息
- 回滚方案：按 endpoint/repository 粒度回退

## 7. 验证方案

- `pytest backend/tests -q`
- 手工验接口：注册登录 -> 上传 -> 版本 -> 标签 -> 分组 -> 分享 -> 审计

## 8. 交付清单

- 代码文件：后端 endpoint/repository/tests
- 文档文件：`docs/前后端对接-待确认问题.md`
- 变更说明：P0 对接阻塞项清零（除 P1）
