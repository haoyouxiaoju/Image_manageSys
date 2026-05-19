<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAssetStore } from '@/stores/assets'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()
const store = useAssetStore()

const showDialog = ref(false)
const newCol = ref({ name: '', desc: '' })

onMounted(() => { store.fetchCollections() })

async function createCollection() {
  if (!newCol.value.name.trim()) { ElMessage.warning('请输入分组名称'); return }
  await store.createCollection(newCol.value.name, newCol.value.desc)
  ElMessage.success('分组已创建')
  showDialog.value = false
  newCol.value = { name: '', desc: '' }
}

function viewCollection(c: { id: number }) {
  router.push(`/collection/${c.id}`)
}
</script>

<template>
  <div class="collections-page">
  <div class="page-toolbar" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
    <h2 style="font-size:20px">分组管理</h2>
    <el-button type="primary" :icon="Plus" @click="showDialog = true" :disabled="auth.isGuest">新建分组</el-button>
  </div>

  <div class="collections-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">
    <div v-for="c in store.collections" :key="c.id" class="collection-card" @click="viewCollection(c)">
      <div class="col-header">
        <span class="col-name">{{ c.name }}</span>
        <el-tag size="small">{{ c.asset_count }} 项</el-tag>
      </div>
      <div class="col-desc">{{ c.description }}</div>
      <div class="col-thumbs">
        <img
          v-for="a in store.getCollectionAssets(c).slice(0, 4)"
          :key="a.id"
          :src="a.thumb"
        >
      </div>
      <div class="col-meta">创建于 {{ c.created_at?.substring(0, 10) }} · {{ c.creator }}</div>
    </div>
  </div>
  <el-empty v-if="store.collections.length === 0" description="暂无分组" />

  <el-dialog v-model="showDialog" title="新建分组" width="440px">
    <el-form label-width="70px">
      <el-form-item label="名称"><el-input v-model="newCol.name" placeholder="例如：2026春季新品素材" /></el-form-item>
      <el-form-item label="描述"><el-input v-model="newCol.desc" type="textarea" :rows="2" placeholder="分组用途说明" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showDialog = false">取消</el-button>
      <el-button type="primary" @click="createCollection">创建</el-button>
    </template>
  </el-dialog>
  </div>
</template>

<style scoped>
.collections-page {
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .page-toolbar {
    align-items: flex-start !important;
    flex-direction: column;
    gap: 12px;

    :deep(.el-button) {
      width: 100%;
    }
  }

  .collections-grid {
    grid-template-columns: 1fr !important;
    gap: 12px !important;
  }
}
</style>
