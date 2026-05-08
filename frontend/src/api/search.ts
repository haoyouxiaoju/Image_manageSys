import client from './client'
import type { BackendAsset } from './assets'

export interface SearchTextRequest {
  query: string
  page?: number
  page_size?: number
}

export interface SearchTextItem {
  asset: BackendAsset
  score: number
}

export interface SearchTextResponse {
  items: SearchTextItem[]
  total: number
  page: number
  page_size: number
}

export const searchApi = {
  /** 文本语义搜索 */
  searchText(data: SearchTextRequest) {
    return client.post<SearchTextResponse>('/search/text', data)
  },
}
