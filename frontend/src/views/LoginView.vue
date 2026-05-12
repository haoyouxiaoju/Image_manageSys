<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const mode = ref<'login' | 'register'>(
  (route.query.mode as string) === 'register' ? 'register' : 'login'
)
const form = ref({ username: '', password: '', confirmPassword: '' })
const loading = ref(false)

function switchMode(m: 'login' | 'register') {
  mode.value = m
  form.value = { username: '', password: '', confirmPassword: '' }
}

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

async function handleRegister() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (form.value.password !== form.value.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (form.value.password.length < 8) {
    ElMessage.warning('密码至少需要 8 位')
    return
  }
  loading.value = true
  try {
    await auth.register({ username: form.value.username, password: form.value.password })
    ElMessage.success('注册成功，已自动登录')
    router.push('/assets')
  } catch (e: any) {
    const msg = e?.response?.data?.error?.message || '注册失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div style="display:flex;justify-content:center;align-items:center;height:100%">
    <div style="width:400px;background:#fff;border-radius:8px;padding:40px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
      <h2 style="text-align:center;margin-bottom:4px;font-size:20px">
        {{ mode === 'login' ? '登录' : '注册' }}
      </h2>
      <p style="text-align:center;color:#909399;font-size:13px;margin-bottom:24px">
        Image 企业素材库管理系统
      </p>

      <el-form label-width="0" @submit.prevent>
        <!-- 模式切换 -->
        <div style="display:flex;gap:0;margin-bottom:20px;border-radius:6px;overflow:hidden;border:1px solid #dcdfe6">
          <div
            style="flex:1;text-align:center;padding:8px 0;cursor:pointer;font-size:14px;transition:all 0.2s"
            :style="mode === 'login' ? 'background:#409EFF;color:#fff' : 'background:#fff;color:#606266'"
            @click="switchMode('login')"
          >登录</div>
          <div
            style="flex:1;text-align:center;padding:8px 0;cursor:pointer;font-size:14px;transition:all 0.2s"
            :style="mode === 'register' ? 'background:#409EFF;color:#fff' : 'background:#fff;color:#606266'"
            @click="switchMode('register')"
          >注册</div>
        </div>

        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名（3-32位字母数字下划线）" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码（至少8位）" show-password size="large" />
        </el-form-item>
        <el-form-item v-if="mode === 'register'">
          <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" show-password size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading"
            @click="mode === 'login' ? handleLogin() : handleRegister()">
            {{ mode === 'login' ? '登录' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <p style="text-align:center;font-size:12px;color:#c0c4cc;margin-top:8px">
        {{ mode === 'login' ? '没有账号？' : '已有账号？' }}
        <span style="color:#409EFF;cursor:pointer" @click="switchMode(mode === 'login' ? 'register' : 'login')">
          {{ mode === 'login' ? '立即注册' : '去登录' }}
        </span>
      </p>
    </div>
  </div>
</template>
