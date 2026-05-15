<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAssetStore } from '@/stores/assets'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const store = useAssetStore()

const localSearch = ref(store.globalSearch)

function onGlobalSearch() {
  store.globalSearch = localSearch.value
  store.currentPage = 1
  if (route.path !== '/assets') {
    router.push('/assets')
  }
}

watch(() => store.globalSearch, (v) => { localSearch.value = v })

function handleLogout() {
  auth.logout()
  store.clearFilters()
  router.push('/assets')
}

function goLogin() {
  router.push('/login')
}

const roleColors: Record<string, string> = {
  admin: '#FF3B30',
  editor: '#FF9500',
  guest: '#86868B',
}
</script>

<template>
  <header class="top-nav">
    <!-- Logo -->
    <div class="logo" @click="router.push('/assets')" style="cursor: pointer">
      <div class="logo-icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="2" y="2" width="5" height="5" rx="1" fill="white" opacity="0.9"/>
          <rect x="9" y="2" width="5" height="5" rx="1" fill="white" opacity="0.6"/>
          <rect x="2" y="9" width="5" height="5" rx="1" fill="white" opacity="0.6"/>
          <rect x="9" y="9" width="5" height="5" rx="1" fill="white" opacity="0.3"/>
        </svg>
      </div>
      <span>Image<span style="font-weight: 300; color: var(--text-secondary)">.</span></span>
    </div>

    <!-- Search -->
    <div style="position: relative; display: flex; align-items: center; width: 260px">
      <svg
        style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-tertiary); pointer-events: none; z-index: 1"
        width="14" height="14" viewBox="0 0 16 16" fill="none"
      >
        <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M11 11L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <input
        v-model="localSearch"
        class="search-input"
        placeholder="搜索素材…"
        @keyup.enter="onGlobalSearch"
        @input="store.globalSearch = localSearch"
      />
      <button
        v-if="localSearch"
        @click="localSearch=''; store.globalSearch=''"
        style="position: absolute; right: 8px; background: none; border: none; cursor: pointer; color: var(--text-tertiary); font-size: 11px; padding: 4px; line-height: 1"
      >✕</button>
    </div>

    <!-- Right Side -->
    <div class="top-right">
      <span
        v-if="auth.isLoggedIn"
        class="role-badge"
        :style="{ background: roleColors[auth.role] + '18', color: roleColors[auth.role] }"
      >
        {{ auth.roleLabel }}
      </span>

      <template v-if="auth.isLoggedIn">
        <el-dropdown trigger="click">
          <span class="user-chip">
            <span class="user-avatar">{{ auth.user?.username?.charAt(0).toUpperCase() }}</span>
            <span class="user-name">{{ auth.user?.username }}</span>
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style="opacity: 0.5">
              <path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled style="cursor: default">
                <span style="font-size: 11px; color: var(--text-tertiary)">
                  {{ (auth.user as any)?.email || '未设置邮箱' }}
                </span>
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>

      <template v-else>
        <el-button size="small" text @click="goLogin" style="font-size: 13px; color: var(--text-secondary)">登录</el-button>
        <el-button
          size="small"
          @click="router.push('/login')"
          style="background: var(--accent); color: white; border: none; border-radius: 8px; font-size: 13px;"
        >
          注册
        </el-button>
      </template>
    </div>
  </header>
</template>

<style scoped>
.role-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.02em;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 150ms;
}

.user-chip:hover {
  background: rgba(0, 0, 0, 0.05);
}

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-purple));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}
</style>