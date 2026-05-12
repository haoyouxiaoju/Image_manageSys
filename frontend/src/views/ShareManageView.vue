<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAssetStore } from '@/stores/assets'
import { shareApi, type ShareLinkResponse } from '@/api/share'

const store = useAssetStore()

const shareLinks = ref<ShareLinkResponse[]>([])

onMounted(() => {
  fetchShareLinks()
})

async function fetchShareLinks() {
  try {
    const res = await shareApi.list()
    shareLinks.value = res.data
  } catch {
    // ignore
  }
}

function copyUrl(link: ShareLinkResponse) {
  const fullUrl = window.location.origin + link.url
  navigator.clipboard.writeText(fullUrl).then(() => ElMessage.success('链接已复制'))
}

async function revokeLink(link: ShareLinkResponse) {
  try {
    await ElMessageBox.confirm('确定撤销该分享链接吗？撤销后链接立即失效。', '确认撤销', { type: 'warning' })
    await shareApi.revoke(link.id)
    link.is_active = false
    ElMessage.success('分享链接已撤销')
  } catch {
    // cancelled
  }
}

// 新建分享链接对话框
const showCreateDialog = ref(false)
const createForm = ref({ assetId: 0, expiresIn: 24 })
const assetSearchQuery = ref('')

const filteredAssetsForShare = ref<{ id: number; name: string }[]>([])
function onSearchAssets(q: string) {
  assetSearchQuery.value = q
  if (!q) { filteredAssetsForShare.value = []; return }
  const kw = q.toLowerCase()
  filteredAssetsForShare.value = store.allAssets
    .filter(a => a.name.toLowerCase().includes(kw))
    .slice(0, 10)
    .map(a => ({ id: a.id, name: a.name }))
}

function openCreateDialog() {
  createForm.value = { assetId: 0, expiresIn: 24 }
  filteredAssetsForShare.value = store.allAssets.slice(0, 10).map(a => ({ id: a.id, name: a.name }))
  showCreateDialog.value = true
}

async function confirmCreateLink() {
  if (!createForm.value.assetId) { ElMessage.warning('请选择素材'); return }
  try {
    await shareApi.create({
      asset_id: createForm.value.assetId,
      expires_in_hours: createForm.value.expiresIn,
    })
    ElMessage.success('分享链接已创建')
    showCreateDialog.value = false
    await fetchShareLinks()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  }
}
</script>

<template>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
    <h2 style="font-size:20px">分享管理</h2>
    <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建分享链接</el-button>
  </div>

  <div class="audit-table">
    <el-table :data="shareLinks" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="asset_name" label="目标素材" />
      <el-table-column prop="url" label="链接" min-width="200">
        <template #default="{ row }">
          <span style="font-size:13px;font-family:monospace;color:#409EFF">{{ window?.location?.origin || '' }}{{ row.url }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="150" />
      <el-table-column prop="expires_at" label="过期时间" width="150" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '有效' : '已失效' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="copyUrl(row)">复制</el-button>
          <el-button v-if="row.is_active" size="small" type="danger" @click="revokeLink(row)">撤销</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>

  <el-dialog v-model="showCreateDialog" title="新建分享链接" width="460px">
    <el-form label-width="80px">
      <el-form-item label="选择素材">
        <el-select
          v-model="createForm.assetId"
          filterable
          remote
          :remote-method="onSearchAssets"
          placeholder="搜索素材名称..."
          style="width:100%"
        >
          <el-option v-for="a in filteredAssetsForShare" :key="a.id" :label="a.name" :value="a.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="过期时间">
        <el-select v-model="createForm.expiresIn" style="width:100%">
          <el-option label="1 小时" :value="1" />
          <el-option label="6 小时" :value="6" />
          <el-option label="24 小时" :value="24" />
          <el-option label="72 小时" :value="72" />
          <el-option label="7 天" :value="168" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showCreateDialog = false">取消</el-button>
      <el-button type="primary" @click="confirmCreateLink">创建链接</el-button>
    </template>
  </el-dialog>

  <el-empty v-if="shareLinks.length === 0" description="暂无分享链接" />
</template>
