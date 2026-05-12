import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动附加 JWT token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 防抖：避免多个 401 同时触发多次登录跳转
let _loggingOut = false

// 响应拦截器：统一错误处理
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    switch (status) {
      case 401:
        // 避免并发 401 重复处理
        if (_loggingOut) break
        _loggingOut = true
        try {
          // 先验证 token 是否真的失效（可能是后端瞬时不可用）
          const ok = await verifyToken()
          if (ok) {
            // token 仍有效，重放原请求
            _loggingOut = false
            return client.request(error.config)
          }
        } catch {
          // /auth/me 也失败了，token 确实失效
        }
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        localStorage.removeItem('role')
        _loggingOut = false
        window.location.hash = '#/login'
        ElMessage.error('登录已过期，请重新登录')
        break
      case 403:
        ElMessage.error('权限不足：' + (detail || '无法执行此操作'))
        break
      case 422:
        ElMessage.error('输入验证失败：' + (detail || '请检查输入'))
        break
      case 500:
        ElMessage.error('服务器内部错误，请稍后重试')
        break
      default:
        if (!error.config?.silent) {
          ElMessage.error(detail || '请求失败')
        }
    }
    return Promise.reject(error)
  },
)

/** 用当前 token 调 /auth/me 验证是否仍然有效 */
async function verifyToken(): Promise<boolean> {
  const token = localStorage.getItem('access_token')
  if (!token) return false
  try {
    await axios.get('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 5000,
    })
    return true
  } catch {
    return false
  }
}

export default client
