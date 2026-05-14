<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAssetStore } from '@/stores/assets'
import AssetCard from '@/components/common/AssetCard.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'

const router = useRouter()
const store = useAssetStore()

onMounted(() => {
  store.fetchAssets()
})

function goDetail(id: number) {
  router.push(`/asset/${id}`)
}
</script>

<template>
  <div class="page-assets">
    <!-- Error -->
    <div v-if="store.error" class="error-banner animate-in">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.3"/>
        <path d="M8 5V8.5M8 10.5V11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <span>{{ store.error }}</span>
      <button @click="store.fetchAssets()">重试</button>
    </div>

    <!-- Stats -->
    <div class="stat-cards" v-if="!store.loading">
      <StatCard icon="grid" color="blue"   :num="store.allAssets.length"   label="素材总数" />
      <StatCard icon="plus" color="green"  :num="store.monthNewCount"      label="本月新增" />
      <StatCard icon="tag"  color="orange" :num="store.allTags.length"     label="标签数" />
      <StatCard icon="spark" color="purple" :num="store.visionReadyCount"   label="AI 已索引" />
    </div>
    <LoadingSkeleton v-else type="cards" :count="4" />

    <!-- Tag Filter -->
    <div class="tag-filter animate-in" v-if="!store.loading && store.allTags.length > 0">
      <div class="tag-filter-title">
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
          <path d="M2 4.5C2 3.67 2.67 3 3.5 3H6L7.5 5H12.5C13.33 5 14 5.67 14 6.5V11.5C14 12.33 13.33 13 12.5 13H3.5C2.67 13 2 12.33 2 11.5V4.5Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
        </svg>
        标签筛选
      </div>
      <div class="tag-list">
        <span
          v-for="t in store.allTags"
          :key="t"
          class="tag-chip"
          :class="{ active: store.selectedTags.includes(t) }"
          @click="store.toggleTag(t)"
        >{{ t }}</span>
      </div>
    </div>

    <!-- Grid -->
    <div class="asset-grid">
      <AssetCard
        v-for="a in store.pagedAssets"
        :key="a.id"
        :asset="a"
        @click="goDetail(a.id)"
      />
    </div>

    <div v-if="store.filteredAssets.length === 0" class="empty-state animate-in">
      <svg class="empty-icon" width="40" height="40" viewBox="0 0 40 40" fill="none">
        <rect x="6" y="6" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
        <rect x="22" y="6" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
        <rect x="6" y="22" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
        <rect x="22" y="22" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
      </svg>
      <div class="empty-title">没有匹配的素材</div>
      <div class="empty-desc">尝试调整筛选标签，或上传新素材</div>
    </div>

    <!-- Pagination -->
    <div class="pagination-wrap" v-if="store.filteredAssets.length > store.pageSize">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="store.filteredAssets.length"
        :page-size="store.pageSize"
        v-model:current-page="store.currentPage"
      />
    </div>
  </div>
</template>

<style scoped>
.page-assets {
  max-width: 1400px;
  margin: 0 auto;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.2);
  border-radius: var(--radius-md);
  color: var(--danger);
  font-size: 13px;
  margin-bottom: var(--space-5);

  button {
    background: none;
    border: none;
    color: var(--accent);
    cursor: pointer;
    font-weight: 500;
    margin-left: auto;
  }
}
</style>