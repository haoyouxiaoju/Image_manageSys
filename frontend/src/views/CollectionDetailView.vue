<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAssetStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'
import type { Asset, Collection } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useAssetStore()
const auth = useAuthStore()

const collection = ref<Collection | undefined>(undefined)
const assets = ref<Asset[]>([])
const sortBy = ref<'date_desc' | 'date_asc' | 'name'>('date_desc')
const filterTag = ref('')

onMounted(() => {
  collection.value = store.getCollectionById(Number(route.params.id))
  if (collection.value) {
    assets.value = store.getCollectionAssets(collection.value)
  }
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
      </div>
    </div>

    <!-- 标签筛选 -->
    <div class="tag-filter" v-if="allTags.length > 0">
      <div class="title">筛选标签</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <el-tag
          :type="filterTag ? 'info' : ''" :effect="filterTag ? 'plain' : 'dark'"
          style="cursor:pointer" @click="filterTag = ''"
        >全部</el-tag>
        <el-tag v-for="t in allTags" :key="t"
          :type="filterTag === t ? '' : 'info'"
          :effect="filterTag === t ? 'dark' : 'plain'"
          style="cursor:pointer"
          @click="filterTag = filterTag === t ? '' : t"
        >{{ t }}</el-tag>
      </div>
    </div>

    <!-- 素材网格 -->
    <div class="asset-grid">
      <div v-for="a in sortedAndFiltered" :key="a.id" class="asset-card" @click="goDetail(a.id)">
        <img :src="a.thumb" :alt="a.name" class="thumb" loading="lazy">
        <div class="card-info">
          <div class="card-name">{{ a.name }}</div>
          <div class="card-meta"><span>{{ a.author }}</span><span>{{ a.date }}</span></div>
          <div class="card-tags">
            <el-tag v-for="t in a.tags" :key="t" size="small">{{ t }}</el-tag>
          </div>
        </div>
      </div>
    </div>
    <el-empty v-if="sortedAndFiltered.length === 0" description="该分组没有匹配的素材" />
  </div>
  <el-empty v-else description="分组未找到" />
</template>
