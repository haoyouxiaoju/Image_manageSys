<script setup lang="ts">
defineProps<{
  icon: string
  color: 'blue' | 'green' | 'orange' | 'purple'
  num: number
  label: string
}>()

const icons: Record<string, string> = {
  grid: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <rect x="3" y="3" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
    <rect x="11" y="3" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
    <rect x="3" y="11" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
    <rect x="11" y="11" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
  </svg>`,
  plus: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M10 4V16M4 10H16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  </svg>`,
  tag: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M3 3.5H9L16 10.5V15.5C16 16.33 15.33 17 14.5 17H5.5C4.67 17 4 16.33 4 15.5V4.5C4 3.67 4.67 3.5 5.5 3.5H3Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
    <circle cx="6.5" cy="7.5" r="1" fill="currentColor"/>
  </svg>`,
  spark: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M10 2L11.5 7.5L17 8.5L11.5 9.5L10 15L8.5 9.5L3 8.5L8.5 7.5L10 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
  </svg>`,
}
</script>

<template>
  <div class="stat-card animate-in">
    <div class="stat-icon" :class="color">
      <span v-html="icons[icon] || icons.spark"></span>
    </div>
    <div class="stat-info">
      <div class="stat-num">{{ num }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </div>
</template>