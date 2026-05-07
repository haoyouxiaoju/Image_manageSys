import client from './client'
import type { Asset, PaginatedResponse } from '@/types'

export const assetsApi = {
  /** 获取素材列表（分页 + 标签筛选 + 全局搜索） */
  getAssets(params: {
    page?: number
    page_size?: number
    tags?: string[]
    q?: string
  }) {
    return client.get<PaginatedResponse<Asset>>('/assets', { params })
  },

  /** 获取素材详情 */
  getAsset(id: number) {
    return client.get<Asset>(`/assets/${id}`)
  },

  /** 更新素材元数据 */
  updateAsset(id: number, data: Partial<Pick<Asset, 'name' | 'desc' | 'tags' | 'source'>>) {
    return client.put<Asset>(`/assets/${id}`, data)
  },

  /** 删除素材 */
  deleteAsset(id: number) {
    return client.delete(`/assets/${id}`)
  },

  /** 上传素材（FormData） */
  uploadAsset(formData: FormData) {
    return client.post<Asset>('/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    })
  },
}
