import client from './client'

export interface ClipStatus {
  enabled: boolean
  provider: string
  model_name: string
  model_version: string
  initialized: boolean
  ready: boolean
  last_error: string | null
}

export interface ClipAnalyzeResponse {
  provider: string
  model: string
  model_version: string
  prompt: string
  summary: string
  keywords: string[]
}

export const clipApi = {
  getStatus() {
    return client.get<ClipStatus>('/clip/status')
  },
  analyze(formData: FormData) {
    return client.post<ClipAnalyzeResponse>('/clip/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })
  },
}
