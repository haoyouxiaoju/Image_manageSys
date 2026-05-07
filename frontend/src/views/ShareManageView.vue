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
  { id:1, assetId:1, assetName:'科技感蓝色背景图', token:'abc123', url:'https://clip-image.example.com/share/abc123', created:'2026-05-07 14:30', expiresAt:'2026-05-08 14:30', isActive:true },
  { id:2, assetId:4, assetName:'双十一促销海报',   token:'def456', url:'https://clip-image.example.com/share/def456', created:'2026-05-06 10:15', expiresAt:'2026-05-07 10:15', isActive:false },
  { id:3, assetId:7, assetName:'春季新品发布海报',   token:'ghi789', url:'https://clip-image.example.com/share/ghi789', created:'2026-05-05 16:00', expiresAt:'2026-05-06 16:00', isActive:true },
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

function createShareLink() {
  ElMessage.info('模拟创建：POST /api/v1/share-links { asset_id, expires_in_hours }')
}
</script>

<template>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
    <h2 style="font-size:20px">分享管理</h2>
    <el-button type="primary" :icon="Plus" @click="createShareLink">新建分享链接</el-button>
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
  <el-empty v-if="shareLinks.length === 0" description="暂无分享链接" />
</template>
