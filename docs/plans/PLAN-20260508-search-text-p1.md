# PLAN-20260508-search-text-p1

## 1. 任务背景

前后端对接文档中 `POST /api/v1/search/text` 仍是未完成项，前端 SearchView 还在使用本地模拟，无法进入真实语义检索联调。

## 2. 目标与验收结果

- 目标 1：实现 `POST /api/v1/search/text`。
- 目标 2：复用已落地的 CLIP 向量数据，提供文本语义检索结果。
- 目标 3：回填前后端对接文档状态为已就绪。

验收标准（必须可验证）：
- [x] `POST /api/v1/search/text` 可用，支持分页参数
- [x] 返回结构：`{ items: [{ asset, score }], total, page, page_size }`
- [x] 与当前 CLIP 数据结构兼容（无向量数据素材不参与语义排序）
- [x] 后端测试通过
- [x] 对接文档中 search/text 状态改为已就绪

## 3. 本次范围 / 非范围

### 3.1 In Scope
- 文本编码（query -> embedding）
- 与已存储素材 embedding 相似度计算与分页
- 文档状态回填

### 3.2 Out of Scope
- FAISS 索引与大规模性能优化
- 复杂检索过滤策略（多条件过滤、重排模型）

## 4. 技术方案

- 在 `ClipService` 增加文本编码能力（mock/chinese_clip 双 provider）。
- 在 `clip_repository` 增加“可检索素材+embedding”读取能力。
- 新增 endpoint `backend/app/api/v1/endpoints/search.py` 并注册路由 `/api/v1/search/text`。
- 使用余弦相似度在应用层排序并分页返回。

## 5. 任务拆解与推进顺序

1. 扩展 CLIP service 与 repository
2. 实现 search endpoint 与路由注册
3. 增加测试覆盖
4. 更新对接文档与 README

## 6. 风险与回滚

- 风险点：embedding 维度不一致导致检索结果异常
- 监控点：接口返回 total 与 items 数量、score 排序正确性
- 回滚方案：按 `search.py` + service/repository 变更粒度回退

## 7. 验证方案

- `python -m pytest backend/tests -q`
- 手工：上传两张图片后调用 `/api/v1/search/text` 检查返回和分页

## 8. 交付清单

- 代码文件：`clip_service.py`、`clip_repository.py`、`search.py`、`router.py`、`test_app_baseline.py`
- 文档文件：`docs/前后端对接-待确认问题.md`、`README.md`
- 结果：前后端对接清单仅剩前端切换工作，无后端接口阻塞

## 9. 完成记录

| 完成日期 | 状态 | 说明 |
|---------|------|------|
| 2026-05-08 | ✅ 已完成 | 全部 5 项验收标准达标，后端 search API 就绪，详见 `docs/decisions/2026-05-08-前端对接实施步骤-已完成.md` 第 6 项 |
