# PLAN-20260507-assets-crud-m2

## 1. 任务背景

后端已具备认证与基础 RBAC，但素材主链路（上传、分页列表、详情、编辑、删除）尚未落地，前后端无法进入真实联调。

## 2. 目标与验收结果

- 目标 1：实现素材上传接口（图片类型与大小校验）。
- 目标 2：实现素材分页列表、详情、编辑、删除接口。
- 目标 3：落实删除权限（admin 全量，editor 仅自己上传）。

验收标准（必须可验证）：
- [x] `POST /api/v1/assets/upload` 可成功入库并返回素材信息
- [x] `GET /api/v1/assets` 支持 `page/page_size` 分页（默认每页 10 条）
- [x] `GET/PUT/DELETE /api/v1/assets/{id}` 可用，权限符合规则
- [x] 测试覆盖上传、分页、权限拒绝与删除场景

## 3. 本次范围 / 非范围

### 3.1 In Scope
- 素材元数据表与本地文件存储
- 素材 CRUD API
- 最小权限策略（guest 只读，editor 自己可改删，admin 全量）

### 3.2 Out of Scope
- 标签系统、分组系统、分享系统
- CLIP 向量化与检索逻辑

## 4. 技术方案

- `assets` 表持久化素材元数据
- 本地文件存储目录读取 `settings.uploads_dir`
- 上传阶段校验 MIME 与大小（JPG/PNG/WebP，<=20MB）
- 列表接口以 SQL `LIMIT/OFFSET` 实现分页

## 5. 任务拆解与推进顺序

1. 扩展配置与数据库（uploads_dir + assets 表）
2. 新增仓储层与 assets endpoint
3. 路由注册与权限判定接入
4. 测试与 README 同步

## 6. 风险与回滚

- 风险点：文件写入失败或权限判断遗漏
- 监控点：上传接口错误码、删除后文件清理
- 回滚方案：仅新增表与接口，可按文件回退

## 7. 验证方案

- 单元/接口测试：pytest 覆盖核心路径
- 手工验证：注册登录 -> 上传 -> 列表 -> 编辑 -> 删除
- 边界场景：超限文件、非法格式、非所有者删除

## 8. 交付清单

- 代码文件：config/database/repository/assets endpoint/tests
- 文档文件：README（接口与运行说明补充）
- 变更说明：完成 M2 素材 CRUD 最小闭环
