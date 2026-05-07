<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAssetStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import type { Asset, Collection } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useAssetStore()
const auth = useAuthStore()

const collection = ref<Collection | undefined>(undefined)
const assets = ref<Asset[]>([])
const sortBy = ref<'date_desc' | 'date_asc' | 'name'>('date_desc')
const filterTag = ref('')

function refreshAssets() {
  if (collection.value) {
    assets.value = store.getCollectionAssets(collection.value)
  }
}

onMounted(() => {
  collection.value = store.getCollectionById(Number(route.params.id))
  refreshAssets()
})

const allTags = computed(() => {
  const s = new Set<string>()
  assets.value.forEach(a => a.tags.forEach(t => s.add(t)))
  return [...s]
})

const sortedAndFiltered = computed(() => {
  let arr = assets.value
  if (filterTag.value) {
    arr = arr.filter(a => a.tags.includes(filterTag.value))
  }
  if (sortBy.value === 'date_desc') {
    arr = [...arr].sort((a, b) => b.date.localeCompare(a.date))
  } else if (sortBy.value === 'date_asc') {
    arr = [...arr].sort((a, b) => a.date.localeCompare(b.date))
  } else if (sortBy.value === 'name') {
    arr = [...arr].sort((a, b) => a.name.localeCompare(b.name, 'zh'))
  }
  return arr
})

function goDetail(id: number) {
  router.push(`/asset/${id}`)
}

// #2: 添加/移除素材
const showAddDialog = ref(false)
const assetSearch = ref('')
const selectedAssetIds = ref<number[]>([])

// 可选素材：不在当前分组中的
const availableAssets = computed(() => {
  const existingIds = collection.value?.assetIds || []
  let arr = store.allAssets.filter(a => !existingIds.includes(a.id))
  if (assetSearch.value) {
    const q = assetSearch.value.toLowerCase()
    arr = arr.filter(a => a.name.toLowerCase().includes(q))
  }
  return arr
})

function openAddDialog() {
  selectedAssetIds.value = []
  assetSearch.value = ''
  showAddDialog.value = true
}

function confirmAddAssets() {
  if (!collection.value || selectedAssetIds.value.length === 0) {
    ElMessage.warning('请选择要添加的素材')
    return
  }
  selectedAssetIds.value.forEach(id => {
    store.addToCollection(collection.value!.id, id)
  })
  refreshAssets()
  ElMessage.success(`已添加 ${selectedAssetIds.value.length} 项素材`)
  showAddDialog.value = false
}

function removeFromCollection(assetId: number) {
  if (!collection.value) return
  store.removeFromCollection(collection.value.id, assetId)
  refreshAssets()
  ElMessage.success('已从分组移除')
}
</script>

<template>
  <div v-if="collection">
    <el-button :icon="ArrowLeft" @click="router.push('/collections')" style="margin-bottom:16px">返回分组列表</el-button>

    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
      <div>
        <h2 style="font-size:20px;margin-bottom:4px">{{ collection.name }}</h2>
        <p style="color:#909399;font-size:13px">{{ collection.desc }}</p>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <span style="font-size:12px;color:#909399">排序：</span>
        <el-select v-model="sortBy" size="small" style="width:120px">
          <el-option label="最新优先" value="date_desc" />
          <el-option label="最早优先" value="date_asc" />
          <el-option label="按名称" value="name" />
        </el-select>
        <el-button v-if="!auth.isGuest" size="small" type="primary" :icon="Plus" @click="openAddDialog">添加素材</el-button>
      </div>
    </div>

    <div class="tag-filter" v-if="allTags.length > 0">
      <div class="title">筛选标签</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <el-tag :type="filterTag ? 'info' : ''" :effect="filterTag ? 'plain' : 'dark'" style="cursor:pointer" @click="filterTag = ''">全部</el-tag>
        <el-tag v-for="t in allTags" :key="t"
          :type="filterTag === t ? '' : 'info'"
          :effect="filterTag === t ? 'dark' : 'plain'"
          style="cursor:pointer"
          @click="filterTag = filterTag === t ? '' : t"
        >{{ t }}</el-tag>
      </div>
    </div>

    <div class="asset-grid">
      <div v-for="a in sortedAndFiltered" :key="a.id" class="asset-card" style="position:relative" @click="goDetail(a.id)">
        <img :src="a.thumb" :alt="a.name" class="thumb" loading="lazy">
        <div class="card-info">
          <div class="card-name">{{ a.name }}</div>
          <div class="card-meta"><span>{{ a.author }}</span><span>{{ a.date }}</span></div>
          <div class="card-tags">
            <el-tag v-for="t in a.tags" :key="t" size="small">{{ t }}</el-tag>
          </div>
        </div>
        <el-button v-if="!auth.isGuest"
          style="position:absolute;top:4px;right:4px"
          size="small" type="danger" circle :icon="Close"
          @click.stop="removeFromCollection(a.id)"
        />
      </div>
    </div>
    <el-empty v-if="sortedAndFiltered.length === 0" description="该分组没有匹配的素材" />

    <!-- #2: 添加素材对话框 -->
    <el-dialog v-model="showAddDialog" title="添加素材到分组" width="600px">
      <el-input v-model="assetSearch" placeholder="搜索素材..." clearable style="margin-bottom:16px" />
      <div style="max-height:360px;overflow-y:auto">
        <el-checkbox-group v-model="selectedAssetIds">
          <div v-for="a in availableAssets" :key="a.id"
            style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-bottom:1px solid #f0f0f0;cursor:pointer"
            @click="() => { const i = selectedAssetIds.indexOf(a.id); i >= 0 ? selectedAssetIds.splice(i,1) : selectedAssetIds.push(a.id) }"
          >
            <el-checkbox :value="a.id" @click.stop />
            <img :src="a.thumb" style="width:60px;height:45px;object-fit:cover;border-radius:4px;flex-shrink:0">
            <div style="flex:1;min-width:0">
              <div style="font-size:14px;color:#303133;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ a.name }}</div>
              <div style="font-size:12px;color:#909399">{{ a.date }}</div>
            </div>
          </div>
        </el-checkbox-group>
        <el-empty v-if="availableAssets.length === 0" description="没有可添加的素材" />
      </div>
      <template #footer>
        <span style="color:#909399;font-size:13px">已选 {{ selectedAssetIds.length }} 项</span>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddAssets">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
  <el-empty v-else description="分组未找到" />
</template>
