import client from './client'
import type { BackendAsset } from './assets'

export interface AgentSearchRequest {
  query: string
  page?: number
  page_size?: number
}

export interface AgentSearchResultItem {
  asset: BackendAsset
  score: number
  match_reasons: string[]
}

export interface AgentSearchResponse {
  items: AgentSearchResultItem[]
  reasoning: string
  total: number
  page: number
  page_size: number
}

export const agentApi = {
  search(data: AgentSearchRequest) {
    return client.post<AgentSearchResponse>('/agent/search', data)
  },
}
