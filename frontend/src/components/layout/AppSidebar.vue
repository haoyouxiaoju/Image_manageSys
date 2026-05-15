<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const currentView = computed(() => {
  const path = route.path
  if (path.startsWith('/collection/')) return 'collections'
  if (path.startsWith('/asset/')) return 'assets'
  return path.replace('/', '') || 'assets'
})

function navigate(index: string) {
  router.push(`/${index}`)
}

const menuItems = [
  {
    section: '素材管理',
    items: [
      { key: 'assets', label: '素材库', icon: 'grid' },
      { key: 'collections', label: '分组管理', icon: 'folder' },
      { key: 'search', label: '以文搜图', icon: 'search' },
      { key: 'upload', label: '上传素材', icon: 'upload', requiresAuth: true },
    ],
  },
  {
    section: 'AI 能力',
    items: [
      { key: 'vision-info', label: 'AI 视觉能力说明', icon: 'cpu' },
    ],
  },
]

function isActive(key: string) {
  return currentView.value === key
}

function isDisabled(item: typeof menuItems[0]['items'][0]) {
  return item.requiresAuth && auth.isGuest
}
</script>

<template>
  <aside class="sidebar">
    <template v-for="section in menuItems" :key="section.section">
      <div class="sidebar-section">
        <div class="sidebar-section-title">{{ section.section }}</div>
        <div
          v-for="item in section.items"
          :key="item.key"
          class="sidebar-item"
          :class="{ active: isActive(item.key), disabled: isDisabled(item) }"
          @click="!isDisabled(item) && navigate(item.key)"
        >
          <!-- Grid icon -->
          <svg v-if="item.icon === 'grid'" class="icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/>
            <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/>
            <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/>
            <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          <!-- Folder icon -->
          <svg v-else-if="item.icon === 'folder'" class="icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 4.5C2 3.67 2.67 3 3.5 3H6L7.5 5H12.5C13.33 5 14 5.67 14 6.5V11.5C14 12.33 13.33 13 12.5 13H3.5C2.67 13 2 12.33 2 11.5V4.5Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
          </svg>
          <!-- Search icon -->
          <svg v-else-if="item.icon === 'search'" class="icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="4.5" stroke="currentColor" stroke-width="1.3"/>
            <path d="M10.5 10.5L13.5 13.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <!-- Upload icon -->
          <svg v-else-if="item.icon === 'upload'" class="icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 10V3M8 3L5.5 5.5M8 3L10.5 5.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 11V12C3 12.55 3.45 13 4 13H12C12.55 13 13 12.55 13 12V11" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <!-- CPU icon -->
          <svg v-else-if="item.icon === 'cpu'" class="icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="4" y="4" width="8" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
            <path d="M6 2H10M6 14H10M2 6V10M14 6V10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <span>{{ item.label }}</span>
        </div>
      </div>
    </template>
  </aside>
</template>