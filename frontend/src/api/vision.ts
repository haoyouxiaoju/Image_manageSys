import client from './client'

export interface VisionStatus {
  enabled: boolean
  provider: string
  model_name: string
  model_version: string
  initialized: boolean
  ready: boolean
  last_error: string | null
}

export interface VisionAnalyzeResponse {
  provider: string
  model: string
  model_version: string
  prompt: string
  summary: string
  keywords: string[]
}

export const visionApi = {
  getStatus() {
    return client.get<VisionStatus>('/vision/status')
  },
  analyze(formData: FormData) {
    return client.post<VisionAnalyzeResponse>('/vision/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })
  },
}
