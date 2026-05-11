# PLAN-20260511-qwen-vl-keyword-strategy

## 1. 任务背景

当前方案基于 CLIP 零样本标签匹配，用户希望切换到 Qwen3-VL 按图片直接生成关键词，提升描述准确度并降低标签工程成本。

## 2. 目标与验收结果

- 目标 1：后端图片分析由 CLIP 方案切换为 Qwen3-VL 关键词生成。
- 目标 2：上传链路保存摘要与关键词，供搜索与前端自动填充使用。
- 目标 3：`/search/text` 改为基于关键词/摘要匹配排序。

验收标准（必须可验证）：
- [x] `/api/v1/clip/analyze` 返回 `summary + keywords`
- [x] 上传后 `clip_analysis` 可见关键词与摘要
- [x] `/api/v1/search/text` 可基于关键词检索并分页
- [x] 文档与配置项更新为 Qwen3-VL
- [x] 后端测试通过

## 3. 本次范围 / 非范围

### 3.1 In Scope
- 服务层切换到 Qwen3-VL（含 mock provider）
- 上传、分析、搜索接口策略调整
- 文档与配置更新

### 3.2 Out of Scope
- 前端页面改造
- 向量检索（FAISS）重建

## 4. 技术方案

- 保留现有 `/clip/*` 路径以减少前端改动，内部替换为 Qwen3-VL。
- 通过 DashScope OpenAI 兼容接口调用 `qwen3-vl-plus`。
- 搜索改为关键词/摘要匹配打分，返回结构不变。

## 5. 任务拆解与推进顺序

1. 切换服务实现（Qwen provider + mock）
2. 修改上传/分析接口返回
3. 修改搜索逻辑
4. 更新测试与文档

## 6. 风险与回滚

- 风险点：外部模型接口超时或返回 JSON 结构异常
- 监控点：`/api/v1/clip/status` 的 `ready/last_error`
- 回滚方案：可切换 `CLIP_PROVIDER=mock` 保持业务链路可用

## 7. 验证方案

- `python -m pytest backend/tests -q`
- 手工调用 `/api/v1/clip/status`、`/api/v1/clip/analyze`、`/api/v1/search/text`

## 8. 交付清单

- `backend/app/services/clip_service.py`
- `backend/app/api/v1/endpoints/{clip.py,assets.py,search.py}`
- `backend/app/core/config.py`
- `backend/tests/test_app_baseline.py`
- `README.md`
- `docs/前后端对接-待确认问题.md`
