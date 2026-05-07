<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAssetStore } from '@/stores/assets'
import AssetCard from '@/components/common/AssetCard.vue'
import StatCard from '@/components/common/StatCard.vue'

const router = useRouter()
const store = useAssetStore()

function goDetail(id: number) {
  router.push(`/asset/${id}`)
}
</script>

<template>
  <!-- 统计卡片 -->
  <div class="stat-cards">
    <StatCard icon="PictureFilled" color="blue"  :num="store.allAssets.length" label="素材总数" />
    <StatCard icon="Plus"          color="green"  :num="store.monthNewCount"    label="本月新增" />
    <StatCard icon="Collection"    color="orange" :num="store.allTags.length"   label="标签数" />
    <StatCard icon="Cpu"           color="purple" :num="store.clipReadyCount"   label="CLIP已索引" />
  </div>

  <!-- 标签筛选 -->
  <div class="tag-filter">
    <div class="title">标签筛选</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <el-tag
        v-for="t in store.allTags" :key="t"
        :type="store.selectedTags.includes(t) ? '' : 'info'"
        :effect="store.selectedTags.includes(t) ? 'dark' : 'plain'"
        style="cursor:pointer"
        @click="store.toggleTag(t)"
      >{{ t }}</el-tag>
    </div>
  </div>

  <!-- 素材网格 -->
  <div class="asset-grid">
    <AssetCard v-for="a in store.pagedAssets" :key="a.id" :asset="a" @click="goDetail(a.id)" />
  </div>
  <el-empty v-if="store.filteredAssets.length === 0" description="没有匹配的素材" />

  <!-- 分页 -->
  <div class="pagination-wrap" v-if="store.filteredAssets.length > store.pageSize">
    <el-pagination
      background
      layout="prev, pager, next, total"
      :total="store.filteredAssets.length"
      :page-size="store.pageSize"
      v-model:current-page="store.currentPage"
    />
  </div>
</template>
