// ===== 共享类型定义 =====

export interface User {
  id: number
  username: string
  created_at: string
}

export type Role = 'admin' | 'editor' | 'guest'

export interface AssetVersion {
  version: string
  note: string
  date: string
}

export interface Asset {
  id: number
  name: string
  desc: string
  thumb: string
  author: string
  date: string
  tags: string[]
  source: string
  size: string
  format: string
  visionAnalysis?: {
    provider?: string
    status?: string
    model_name?: string
    prompt?: string
    summary?: string
    keywords?: string[]
  }
  versions: AssetVersion[]
}

export interface SearchResult extends Asset {
  score: number
  matchReasons: string[]
}

export interface Collection {
  id: number
  name: string
  description: string
  asset_count: number
  assets?: Asset[]
  creator: string
  created_at: string
}

export interface AuditLog {
  time: string
  user: string
  action: string
  target: string
  ip: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface UploadFormData {
  desc: string
  tags: string[]
  source: string
}
