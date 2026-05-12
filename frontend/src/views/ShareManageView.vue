<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAssetStore } from '@/stores/assets'

const store = useAssetStore()

// 模拟分享链接数据
interface ShareLink {
  id: number
  assetId: number
  assetName: string
  token: string
  url: string
  created: string
  expiresAt: string
  isActive: boolean
}

const shareLinks = ref<ShareLink[]>([
  { id:1, assetId:1, assetName:'科技感蓝色背景图', token:'abc123', url:'https://image.example.com/share/abc123', created:'2026-05-07 14:30', expiresAt:'2026-05-08 14:30', isActive:true },
  { id:2, assetId:4, assetName:'双十一促销海报',   token:'def456', url:'https://image.example.com/share/def456', created:'2026-05-06 10:15', expiresAt:'2026-05-07 10:15', isActive:false },
  { id:3, assetId:7, assetName:'春季新品发布海报',   token:'ghi789', url:'https://image.example.com/share/ghi789', created:'2026-05-05 16:00', expiresAt:'2026-05-06 16:00', isActive:true },
])

function copyUrl(link: ShareLink) {
  navigator.clipboard.writeText(link.url).then(() => ElMessage.success('链接已复制'))
}

function revokeLink(link: ShareLink) {
  ElMessageBox.confirm('确定撤销该分享链接吗？撤销后链接立即失效。', '确认撤销', { type: 'warning' }).then(() => {
    link.isActive = false
    ElMessage.success('分享链接已撤销')
  }).catch(() => {})
}

// #3: 新建分享链接对话框
const showCreateDialog = ref(false)
const createForm = ref({ assetId: 0, expiresIn: 24 })
const assetSearchQuery = ref('')

const filteredAssetsForShare = ref<{ id:number; name:string }[]>([])
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

function confirmCreateLink() {
  if (!createForm.value.assetId) { ElMessage.warning('请选择素材'); return }
  const asset = store.getAssetById(createForm.value.assetId)
  if (!asset) return
  const token = Math.random().toString(36).substring(2, 14)
  const now = new Date()
  const expires = new Date(now.getTime() + createForm.value.expiresIn * 3600000)
  const fmt = (d: Date) => d.toISOString().replace('T', ' ').substring(0, 16)

  shareLinks.value.unshift({
    id: Date.now(),
    assetId: asset.id,
    assetName: asset.name,
    token,
    url: `https://image.example.com/share/${token}`,
    created: fmt(now),
    expiresAt: fmt(expires),
    isActive: true,
  })
  ElMessage.success('分享链接已创建')
  showCreateDialog.value = false
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
      <el-table-column prop="assetName" label="目标素材" />
      <el-table-column prop="url" label="链接" min-width="200">
        <template #default="{ row }">
          <span style="font-size:13px;font-family:monospace;color:#409EFF">{{ row.url }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created" label="创建时间" width="150" />
      <el-table-column prop="expiresAt" label="过期时间" width="150" />
      <el-table-column prop="isActive" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
            {{ row.isActive ? '有效' : '已失效' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="copyUrl(row)">复制</el-button>
          <el-button v-if="row.isActive" size="small" type="danger" @click="revokeLink(row)">撤销</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
  <!-- #3: 新建分享链接对话框 -->
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
