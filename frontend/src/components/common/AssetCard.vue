<script setup lang="ts">
import type { Asset } from '@/types'

defineProps<{ asset: Asset }>()
defineEmits<{ click: [] }>()
</script>

<template>
  <div class="asset-card animate-in" @click="$emit('click')">
    <img
      :src="asset.thumb"
      :alt="asset.name"
      class="asset-thumb"
      loading="lazy"
    />
    <span v-if="asset.visionAnalysis?.prompt" class="ai-badge">
      <svg width="8" height="8" viewBox="0 0 8 8" fill="none" style="vertical-align: middle; margin-right: 2px">
        <circle cx="4" cy="4" r="3" fill="white" opacity="0.9"/>
      </svg>
      AI
    </span>
    <div class="asset-body">
      <div class="asset-name">{{ asset.name }}</div>
      <div class="asset-meta">
        <span>{{ asset.author }}</span>
        <span>·</span>
        <span>{{ asset.date }}</span>
      </div>
      <div class="asset-tags">
        <span v-for="t in (asset.tags || []).slice(0, 3)" :key="t" class="asset-tag">{{ t }}</span>
        <span v-if="(asset.tags || []).length > 3" class="asset-tag-more">+{{ asset.tags!.length - 3 }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.asset-tag {
  display: inline-block;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-secondary);
  font-weight: 400;
}

.asset-tag-more {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 20px;
  background: transparent;
  color: var(--text-tertiary);
}
</style>