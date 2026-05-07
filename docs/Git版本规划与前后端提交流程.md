# Git 版本规划与前后端提交流程（执行版）

## 1. 目标

建立统一的 Git 工作流，确保：
- 前后端改动可独立追踪
- 版本可独立发布且可回滚
- 提交记录可用于快速定位问题

## 2. 分支模型

- `main`：生产发布分支（仅接收已验收内容）
- `dev`：集成分支（日常开发合并入口）
- `release/<version>`：发布准备分支
- `hotfix/<topic>`：线上紧急修复

前后端功能分支必须区分：
- 后端：`feature/backend-<topic>`
- 前端：`feature/frontend-<topic>`
- 全链路联动（确需同时改）：`feature/fullstack-<topic>`

## 3. 提交规范（强制区分前后端）

提交信息格式：`<type>(<scope>): <subject>`

- 后端 scope：`backend`, `api`, `auth`, `db`, `search`
- 前端 scope：`frontend`, `ui`, `page`, `state`
- 文档 scope：`docs`

示例：
- `feat(backend): add asset list pagination api`
- `feat(frontend): add asset list pagination ui`
- `fix(auth): validate jwt subject existence`

## 4. 前后端分离提交规则

1. **禁止一个提交同时混入前后端文件**（除 `fullstack` 场景）
2. 同一需求若涉及前后端，至少拆成两个提交：
   - 后端提交（接口、模型、测试）
   - 前端提交（页面、状态、交互）
3. PR 描述中必须标注变更类型：
   - `[Backend]` / `[Frontend]` / `[Fullstack]`
4. `fullstack` PR 必须按提交粒度分层，不能“一个大提交全混合”。

## 5. 版本号与 Tag 规划

### 5.1 版本号

- 系统总版本：`vX.Y.Z`
- 后端版本：`be-vX.Y.Z`
- 前端版本：`fe-vX.Y.Z`

### 5.2 当前启动阶段建议

- 后端基线：`be-v0.1.0`（已具备 auth 基线）
- 前端基线：`fe-v0.1.0`（完成工程化骨架后打标）
- 首个集成版本：`v0.1.0`（前后端首轮联调通过后）

### 5.3 Tag 规则

- 后端独立发布：打 `be-v*`
- 前端独立发布：打 `fe-v*`
- 联合发布：打 `v*`（并在发布说明中关联对应 `be/fe` tag）

## 6. PR 合并策略

- 功能分支 -> `dev`：Squash merge（保持历史整洁）
- `dev` -> `release/*`：Merge commit（保留里程碑上下文）
- `release/*` -> `main`：Merge commit + 打 tag

必备检查：
- 变更范围与 PR 类型一致（Backend/Frontend/Fullstack）
- 关键测试通过
- 文档已同步（接口变更必须更新文档）

## 7. 推进节奏（按规程执行）

每次开发必须遵循：
1. 先提交 Plan（`docs/plans/PLAN-YYYYMMDD-<topic>.md`）
2. Plan 确认后开始编码
3. 按前后端拆分提交
4. PR 验收通过后合并
5. 达到发布条件后打对应 Tag

## 8. 推荐命令示例

```bash
# 创建后端功能分支
git checkout -b feature/backend-assets-crud

# 创建前端功能分支
git checkout -b feature/frontend-assets-page

# 打后端版本标签
git tag be-v0.1.0

# 打前端版本标签
git tag fe-v0.1.0
```

## 9. 后续 Commit 说明要求（强制）

从下一次提交开始，每个 commit 必须带“详细说明”正文，至少包含：

1. **变更目的**：为什么改
2. **变更内容**：改了哪些模块/接口/文件
3. **影响范围**：会影响哪些功能、是否兼容
4. **验证方式**：如何确认改动有效

推荐 commit body 模板：

```text
<type>(<scope>): <subject>

Why:
- ...

What:
- ...
- ...

Impact:
- ...

Validation:
- ...
```
