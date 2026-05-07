import client from './client'

// 后端 AssetResponse 原始格式
export interface BackendAsset {
  id: number
  name: string
  description: string
  source: string
  file_name: string
  file_size: number
  mime_type: string
  uploaded_by: string
  created_at: string
  updated_at: string
  download_url: string
}

export interface BackendAssetList {
  total: number
  page: number
  page_size: number
  items: BackendAsset[]
}

export const assetsApi = {
  /** 获取素材列表 */
  getAssets(params: { page?: number; page_size?: number; query?: string }) {
    return client.get<BackendAssetList>('/assets', { params })
  },

  /** 获取素材详情 */
  getAsset(id: number) {
    return client.get<BackendAsset>(`/assets/${id}`)
  },

  /** 更新素材元数据 */
  updateAsset(id: number, data: { name?: string; description?: string; source?: string }) {
    return client.put<BackendAsset>(`/assets/${id}`, data)
  },

  /** 删除素材 */
  deleteAsset(id: number) {
    return client.delete(`/assets/${id}`)
  },

  /** 上传素材 */
  uploadAsset(formData: FormData, onProgress?: (e: ProgressEvent) => void) {
    return client.post<BackendAsset>('/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
      onUploadProgress: onProgress,
    })
  },
}
