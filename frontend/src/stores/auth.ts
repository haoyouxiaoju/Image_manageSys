import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, Role, LoginCredentials } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // ===== 状态 =====
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const role = ref<Role>((localStorage.getItem('role') as Role) || 'guest')

  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    try { user.value = JSON.parse(savedUser) } catch { /* ignore */ }
  }

  // ===== 计算属性 =====
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => role.value === 'admin')
  const isEditor = computed(() => role.value === 'editor')
  const isGuest = computed(() => role.value === 'guest')
  const roleLabel = computed(() => {
    const map: Record<Role, string> = { admin: '管理员', editor: '编辑', guest: '访客' }
    return map[role.value]
  })

  // ===== 方法 =====
  async function login(credentials: LoginCredentials) {
    const response = await authApi.login(credentials)
    const { access_token } = response.data
    token.value = access_token
    localStorage.setItem('access_token', access_token)
    const meResponse = await authApi.getMe()
    user.value = meResponse.data
    localStorage.setItem('user', JSON.stringify(meResponse.data))
    const apiRole = (meResponse.data as any).role
    if (apiRole && ['admin', 'editor', 'guest'].includes(apiRole)) {
      role.value = apiRole as Role
      localStorage.setItem('role', apiRole)
    }
  }

  /** 注册（注册成功后自动登录） */
  async function register(credentials: LoginCredentials) {
    const response = await authApi.register(credentials)
    const { access_token } = response.data
    token.value = access_token
    localStorage.setItem('access_token', access_token)
    const meResponse = await authApi.getMe()
    user.value = meResponse.data
    localStorage.setItem('user', JSON.stringify(meResponse.data))
    const apiRole = (meResponse.data as any).role
    if (apiRole && ['admin', 'editor', 'guest'].includes(apiRole)) {
      role.value = apiRole as Role
      localStorage.setItem('role', apiRole)
    }
  }

  function logout() {
    token.value = null
    user.value = null
    role.value = 'guest'
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    localStorage.removeItem('role')
  }

  return {
    user, token, role,
    isLoggedIn, isAdmin, isEditor, isGuest, roleLabel,
    login, register, logout,
  }
})
