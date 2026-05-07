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

// 响应拦截器：统一错误处理
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    switch (status) {
      case 401:
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
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

export default client
