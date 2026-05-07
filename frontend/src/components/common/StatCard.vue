<script setup lang="ts">
defineProps<{
  icon: string
  color: 'blue' | 'green' | 'orange' | 'purple'
  num: number
  label: string
}>()
</script>

<template>
  <div class="stat-card">
    <div class="icon-box" :class="color">
      <el-icon><component :is="icon" /></el-icon>
    </div>
    <div class="info">
      <div class="num">{{ num }}</div>
      <div class="label">{{ label }}</div>
    </div>
  </div>
</template>
