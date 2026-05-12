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

// 全局搜索：回车时跳转到素材库并触发筛选
function onGlobalSearch() {
  store.globalSearch = localSearch.value
  store.currentPage = 1
  if (route.path !== '/assets') {
    router.push('/assets')
  }
}

// 切换页面时同步搜索框的值
watch(() => store.globalSearch, (v) => { localSearch.value = v })

function handleLogout() {
  auth.logout()
  store.clearFilters()
  router.push('/assets')
}

function goLogin() {
  router.push('/login')
}
</script>

<template>
  <header class="top-nav">
    <div class="logo">
      <span class="dot"></span>
      Image 素材库
    </div>
    <div class="top-right">
      <el-input
        v-model="localSearch"
        placeholder="全局搜索素材..."
        :prefix-icon="Search"
        clearable
        size="small"
        style="width: 260px"
        @keyup.enter="onGlobalSearch"
        @clear="store.globalSearch='';store.currentPage=1"
      />
      <template v-if="auth.isGuest">
        <el-tag type="info" size="small">未登录</el-tag>
        <el-button type="primary" size="small" @click="goLogin">登录</el-button>
        <el-button size="small" @click="router.push('/login?mode=register')">注册</el-button>
      </template>
      <template v-else>
        <el-tag :type="auth.isAdmin ? 'danger' : 'warning'" size="small" effect="dark">
          {{ auth.roleLabel }}
        </el-tag>
        <span style="font-size:11px;color:#a0aec0">
          {{ auth.isAdmin ? '全部管理权限' : '可上传和编辑素材' }}
        </span>
        <el-dropdown trigger="click">
          <span style="color:#fff;cursor:pointer;display:flex;align-items:center;gap:4px">
            <el-icon><UserFilled /></el-icon>
            {{ auth.user?.username || '用户' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>角色：{{ auth.roleLabel }}</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
    </div>
  </header>
</template>
