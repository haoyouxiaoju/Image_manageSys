import client from './client'

export interface BackendCollection {
  id: number
  name: string
  description: string
  asset_count: number
  creator: string
  created_at: string
}

export interface BackendCollectionDetail extends BackendCollection {
  assets: any[]
}

export interface CollectionCreateRequest {
  name: string
  description?: string
}

export interface CollectionUpdateRequest {
  name?: string
  description?: string
}

export const collectionsApi = {
  list() {
    return client.get<BackendCollection[]>('/collections')
  },
  get(id: number) {
    return client.get<BackendCollectionDetail>(`/collections/${id}`)
  },
  create(data: CollectionCreateRequest) {
    return client.post<BackendCollection>('/collections', data)
  },
  update(id: number, data: CollectionUpdateRequest) {
    return client.put<BackendCollection>(`/collections/${id}`, data)
  },
  delete(id: number) {
    return client.delete(`/collections/${id}`)
  },
  addAsset(collectionId: number, assetId: number) {
    return client.post(`/collections/${collectionId}/assets`, { asset_id: assetId })
  },
  removeAsset(collectionId: number, assetId: number) {
    return client.delete(`/collections/${collectionId}/assets/${assetId}`)
  },
}
