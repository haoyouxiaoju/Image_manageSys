<script setup lang="ts">
defineProps<{
  type?: 'cards' | 'table' | 'detail'
  count?: number
}>()
</script>

<template>
  <!-- 卡片骨架 -->
  <div v-if="type === 'cards'" class="asset-grid">
    <div v-for="i in (count || 6)" :key="i" class="skeleton-card">
      <div class="skeleton-thumb"></div>
      <div class="skeleton-info">
        <div class="skeleton-line w80"></div>
        <div class="skeleton-line w50"></div>
        <div class="skeleton-line w60"></div>
      </div>
    </div>
  </div>

  <!-- 表格骨架 -->
  <div v-else-if="type === 'table'" style="background:#fff;border-radius:8px;padding:20px">
    <div v-for="i in (count || 5)" :key="i" style="display:flex;gap:16px;padding:12px 0;border-bottom:1px solid #f0f0f0">
      <div class="skeleton-line" style="width:60px"></div>
      <div class="skeleton-line" style="flex:1"></div>
      <div class="skeleton-line" style="width:120px"></div>
      <div class="skeleton-line" style="width:80px"></div>
    </div>
  </div>

  <!-- 详情骨架 -->
  <div v-else-if="type === 'detail'" style="max-width:720px">
    <div style="width:100%;height:320px;background:#e4e7ed;border-radius:8px;margin-bottom:16px;animation:skeleton-pulse 1.5s infinite"></div>
    <div v-for="i in (count || 6)" :key="i" style="display:flex;gap:20px;margin-bottom:14px">
      <div class="skeleton-line" style="width:50px"></div>
      <div class="skeleton-line" style="width:200px"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-card {
  background: #fff; border-radius: 8px; overflow: hidden;
}
.skeleton-thumb {
  width: 100%; height: 160px; background: #e4e7ed;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}
.skeleton-info { padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; }
.skeleton-line {
  height: 14px; border-radius: 4px; background: #e4e7ed;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}
.w80 { width: 80%; } .w60 { width: 60%; } .w50 { width: 50%; }
@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
