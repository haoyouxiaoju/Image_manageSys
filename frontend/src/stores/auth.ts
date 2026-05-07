import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, Role, LoginCredentials } from '@/types'

// ★ 后端就绪后关闭 mock，走真实 API
const USE_MOCK_AUTH = false

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
    if (USE_MOCK_AUTH) {
      // Mock 模式：根据用户名直接分配角色
      return mockLogin(credentials.username)
    }

    // 真实模式：调用后端 API
    const response = await authApi.login(credentials)
    const { access_token } = response.data
    token.value = access_token
    localStorage.setItem('access_token', access_token)
    const meResponse = await authApi.getMe()
    user.value = meResponse.data
    localStorage.setItem('user', JSON.stringify(meResponse.data))
    // 从 API 返回的 role 字段读取角色（不再根据用户名推断）
    const apiRole = (meResponse.data as any).role
    if (apiRole && ['admin', 'editor', 'guest'].includes(apiRole)) {
      role.value = apiRole as Role
      localStorage.setItem('role', apiRole)
    }
  }

  function mockLogin(username: string) {
    const u = username.toLowerCase()
    let assignedRole: Role = 'guest'
    let displayName = '访客用户'
    let userId = 0

    if (u === 'admin') {
      assignedRole = 'admin'
      displayName = '管理员_张伟'
      userId = 1
    } else if (u === 'editor') {
      assignedRole = 'editor'
      displayName = '编辑_李红'
      userId = 2
    } else if (u === 'guest') {
      assignedRole = 'guest'
      displayName = '访客用户'
      userId = 3
    } else {
      assignedRole = 'guest'
      displayName = username
      userId = 99
    }

    token.value = 'mock_token_' + userId
    localStorage.setItem('access_token', token.value)
    role.value = assignedRole
    localStorage.setItem('role', role.value)
    user.value = { id: userId, username: displayName, created_at: '2026-01-01' }
    localStorage.setItem('user', JSON.stringify(user.value))
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
