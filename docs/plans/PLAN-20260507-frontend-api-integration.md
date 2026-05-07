# PLAN：前端对接后端 API

> 日期：2026-05-07 | 前置：后端素材 CRUD 端点已就绪

---

## 对接范围

| 模块 | 后端状态 | 前端行动 |
|------|---------|---------|
| 认证 | 🟢 login / me | 关掉 mock，走真实 API |
| 素材 CRUD | 🟢 upload/list/detail/update/delete/download | Store 切 API，Upload 改用 FormData |
| 标签 | 🔴 未开发 | 保持 mock |
| 分组 | 🔴 未开发 | 保持 mock |
| 分享 | 🔴 未开发 | 保持 mock |
| 审计 | 🔴 未开发 | 保持 mock |
| 搜索 | 🔴 未开发 | 保持 mock |
| 版本 | 🔴 未开发 | 保持 mock |

---

## 改动方案

### 步骤 1：关掉 mock 认证（1 行改动）

**文件**：`src/stores/auth.ts`
**改动**：`USE_MOCK_AUTH = false`
**效果**：登录走 `POST /api/v1/auth/login`，token 来自真实 JWT

---

### 步骤 2：素材 Store 切换为 API 调用

**文件**：`src/stores/assets.ts`
**改动**：将以下方法从 mock 改为调 `@/api/assets` 模块：

| 方法 | 改前 | 改后 |
|------|------|------|
| `fetchAssets()` | 无（新增） | `GET /api/v1/assets?page&page_size&query` |
| `getAssetById()` | `allAssets.find()` | `GET /api/v1/assets/{id}` |
| `updateAsset()` | 直接改 `allAssets` 数组 | `PUT /api/v1/assets/{id}` |
| `deleteAsset()` | splice 数组 | `DELETE /api/v1/assets/{id}` |
| `addAsset()` | unshift 数组 | 上传成功后自动出现在列表中（由 fetchAssets 刷新） |
| `addVersion()` | 直接改数组 | 暂保持 mock（后端版本端点未就绪） |

**保留 mock 的方法**：tags / collections / search / versions（后端未就绪）

**新增**：
- `loading` / `error` 状态（配合 LoadingSkeleton / useAsyncState）
- `fetchAssets()` 初始化方法（替代 buildMockAssets）

---

### 步骤 3：上传改为 FormData

**文件**：`src/views/UploadView.vue`
**改动**：
- 去掉模拟进度条（setTimeout + setInterval）
- 改为 `FormData` + `axios.post('/api/v1/assets/upload', formData, { onUploadProgress })`
- 使用 `onUploadProgress` 获取真实上传进度
- CLIP 分析面板暂时保留（后续后端加 CLIP 编码后再对接）

---

### 步骤 4：接入加载/错误状态

**文件**：`src/views/AssetsView.vue` / `AssetDetailView.vue`
**改动**：
- 接入 `LoadingSkeleton`（数据加载时展示骨架屏）
- 接入 `el-alert` 错误提示 + 重试按钮
- 空数据用 `el-empty`（已有）

---

## 不变的部分

以下保持 mock 不变，后续后端就绪后按此模式追加：

- SearchView → 保持 `store.doSearch()` 本地模拟
- CollectionsView / CollectionDetailView → 保持 `store.mockCollections`
- ShareManageView → 保持 `shareLinks` ref
- AuditView → 保持 `auditLogs` 静态数据
- AssetDetailView 版本历史 → 保持 mock `versions[]`
- AssetDetailView CLIP 面板 → 保持 mock `clipDesc/clipStyle/clipColor`

---

## 验收标准

- [ ] 关闭 `USE_MOCK_AUTH` 后登录成功，token 来自后端 JWT
- [ ] 素材库页面从 `GET /api/v1/assets` 加载真实数据
- [ ] 分页/搜索参数正确传递给后端
- [ ] 素材详情从 `GET /api/v1/assets/{id}` 加载
- [ ] 编辑素材调用 `PUT /api/v1/assets/{id}`，刷新后生效
- [ ] 删除素材调用 `DELETE /api/v1/assets/{id}`，成功后跳回列表
- [ ] 上传素材使用 FormData + 真实进度条
- [ ] 下载调用 `GET /api/v1/assets/{id}/download`
- [ ] 网络错误时展示错误提示 + 重试按钮
