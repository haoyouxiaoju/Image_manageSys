<script setup lang="ts">
import type { Asset } from '@/types'

defineProps<{ asset: Asset }>()
defineEmits<{ click: [] }>()
</script>

<template>
  <div class="asset-card" @click="$emit('click')">
    <img :src="asset.thumb" :alt="asset.name" class="thumb" loading="lazy">
    <span class="ai-badge" v-if="asset.visionAnalysis?.prompt">AI</span>
    <div class="card-info">
      <div class="card-name">{{ asset.name }}</div>
      <div class="card-meta">
        <span>{{ asset.author }}</span>
        <span>{{ asset.date }}</span>
      </div>
      <div class="card-tags">
        <el-tag v-for="t in asset.tags" :key="t" size="small">{{ t }}</el-tag>
      </div>
    </div>
  </div>
</template>
