<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

// 如果未登录且不在登录页，跳转到登录页
if (auth.isGuest && router.currentRoute.value.path !== '/login') {
  // 素材库等页面允许访客浏览
}
</script>

<template>
  <div class="app-layout">
    <AppHeader />
    <div class="main-layout">
      <AppSidebar />
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>
