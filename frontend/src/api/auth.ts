import client from './client'
import type { LoginCredentials, TokenResponse, User } from '@/types'

export const authApi = {
  /** 登录 */
  login(credentials: LoginCredentials) {
    return client.post<TokenResponse>('/auth/login', credentials)
  },

  /** 注册（MVP 阶段可能仅管理员可用） */
  register(credentials: LoginCredentials) {
    return client.post<TokenResponse>('/auth/register', credentials)
  },

  /** 获取当前用户信息 */
  getMe() {
    return client.get<User>('/auth/me')
  },
}
