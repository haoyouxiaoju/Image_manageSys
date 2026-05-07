<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const currentView = computed(() => route.path.replace('/', '') || 'assets')

function onMenuSelect(index: string) {
  router.push(`/${index}`)
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-title">素材管理</div>
    <el-menu :default-active="currentView" @select="onMenuSelect">
      <el-menu-item index="assets">
        <el-icon><PictureFilled /></el-icon>
        <span>素材库</span>
      </el-menu-item>
      <el-menu-item index="collections">
        <el-icon><Folder /></el-icon>
        <span>分组管理</span>
      </el-menu-item>
      <el-menu-item index="search">
        <el-icon><Search /></el-icon>
        <span>以文搜图</span>
      </el-menu-item>
      <el-menu-item index="upload" :disabled="auth.isGuest">
        <el-icon><UploadFilled /></el-icon>
        <span>上传素材</span>
      </el-menu-item>
    </el-menu>

    <div class="sidebar-title">AI 能力</div>
    <el-menu :default-active="currentView" @select="onMenuSelect">
      <el-menu-item index="clip-info">
        <el-icon><Cpu /></el-icon>
        <span>CLIP 能力说明</span>
      </el-menu-item>
    </el-menu>

    <template v-if="auth.isAdmin">
      <div class="sidebar-title">管理</div>
      <el-menu :default-active="currentView" @select="onMenuSelect">
        <el-menu-item index="audit">
          <el-icon><Document /></el-icon>
          <span>审计日志</span>
        </el-menu-item>
      </el-menu>
    </template>
  </aside>
</template>
