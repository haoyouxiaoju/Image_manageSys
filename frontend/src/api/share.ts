import client from './client'

export interface ShareLinkResponse {
  id: number
  asset_id: number
  asset_name: string
  token: string
  url: string
  created_by: string
  created_at: string
  expires_at: string
  is_active: boolean
}

export const shareApi = {
  list() {
    return client.get<ShareLinkResponse[]>('/share-links')
  },
  create(data: { asset_id: number; expires_in_hours: number }) {
    return client.post<ShareLinkResponse>('/share-links', data)
  },
  revoke(id: number) {
    return client.delete(`/share-links/${id}`)
  },
}
