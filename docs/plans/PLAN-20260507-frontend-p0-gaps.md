# PLAN：前端 P0 功能缺口补全

> 日期：2026-05-07 | 关联：`docs/前端开发进度.md` 待完成 #1~#4

---

## 功能 1：素材版本上传 UI

### 当前状态
- AssetDetailView 展示已有版本历史（只读列表）
- 缺少「上传新版本」入口

### 方案
- 在版本历史区域标题旁加「上传新版本」按钮
- 点击弹出 `el-dialog`，包含：
  - 文件选择器（`el-upload` 或 `<input type=file>`）
  - 版本标签输入（自动建议 v1.0 → v1.1 → v2.0）
  - 变更说明输入
- 提交后调用 `store.addVersion(assetId, version)`，刷新列表

### 涉及文件
- `src/views/AssetDetailView.vue`

### 验收标准
- [ ] 编辑/管理员可见「上传新版本」按钮，访客不可见
- [ ] 点击弹出对话框，含文件选择 + 版本号 + 说明
- [ ] 提交后版本列表新增一条记录
- [ ] 版本号自动递增（当前最高版本 +0.1）

---

## 功能 2：分组内添加/移除素材

### 当前状态
- CollectionDetailView 只展示分组内已有素材，无法增删

### 方案
- 页面右上角加「添加素材」按钮
- 点击弹出 `el-dialog`，内嵌素材选择器：
  - 素材列表（网格或表格）+ 多选 checkbox
  - 搜索/标签过滤
  - 已选计数 + 确认按钮
- 每个素材卡片右上角加「移除」按钮（x 图标）

### 涉及文件
- `src/views/CollectionDetailView.vue`
- `src/stores/assets.ts`（`addToCollection` / `removeFromCollection` 已就绪）

### 验收标准
- [ ] 点击「添加素材」弹出选择对话框
- [ ] 可搜索/筛选素材，支持多选
- [ ] 确认后素材加入分组，网格即时刷新
- [ ] 每个素材卡片有移除按钮，点击后从分组移除
- [ ] 已在该分组中的素材在选择器中标记为已选/禁用

---

## 功能 3：分享管理"新建分享链接"交互

### 当前状态
- ShareManageView 展示已有链接，可复制/撤销
- 「新建分享链接」按钮只是 toast 占位

### 方案
- 点击「新建分享链接」弹出 `el-dialog`：
  - 素材选择器（下拉搜索，列出全部素材）
  - 过期时间选择（1h / 6h / 24h / 72h / 自定义）
  - 确认按钮
- 提交后将新链接加入 shareLinks 列表

### 涉及文件
- `src/views/ShareManageView.vue`
- `src/stores/assets.ts`（需加 `createShareLink` action）

### 验收标准
- [ ] 点击弹出对话框，可搜索选择素材
- [ ] 可选择过期时间（预设 + 自定义）
- [ ] 提交后新链接出现在表格顶部
- [ ] 链接 URL 格式正确（含 token）

---

## 功能 4：统一加载/空/错误状态组件

### 当前状态
- 各视图无加载骨架屏
- 空数据只有 `el-empty`
- 无错误/重试状态

### 方案
- 创建 `src/components/common/LoadingSkeleton.vue`：
  - 接收 `type` prop（cards / table / detail）
  - 渲染对应骨架屏
- 创建 `src/composables/useAsyncState.ts`：
  - `loading` / `error` / `data` 三态管理
  - `execute()` 自动管理状态转换
- 在各视图接入

### 涉及文件
- `src/components/common/LoadingSkeleton.vue`（新建）
- `src/composables/useAsyncState.ts`（新建）
- 各视图（按需接入，P0 先做素材库 + 搜索 + 分组）

### 验收标准
- [ ] LoadingSkeleton 支持 cards / table / detail 三种变体
- [ ] useAsyncState 封装 loading → data → error 状态转换
- [ ] 素材库 + 搜索 + 分组页接入三态
- [ ] Mock 模式下可手动触发 loading/error 验证
