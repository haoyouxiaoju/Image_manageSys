<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()

const form = ref({ username: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.value)
    ElMessage.success('登录成功')
    router.push('/assets')
  } catch {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div style="display:flex;justify-content:center;align-items:center;height:100%">
    <div style="width:380px;background:#fff;border-radius:8px;padding:40px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
      <h2 style="text-align:center;margin-bottom:8px;font-size:20px">登录</h2>
      <p style="text-align:center;color:#909399;font-size:13px;margin-bottom:28px">
        CLIP-Image 企业素材库管理系统
      </p>
      <el-form label-width="0" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名 (admin / editor / guest)" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" show-password size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleLogin">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <p style="text-align:center;font-size:12px;color:#c0c4cc;margin-top:16px">
        原型阶段，使用 admin / editor / guest 用户名即可登录
      </p>
    </div>
  </div>
</template>
