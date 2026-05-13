import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { assetsApi, type BackendAsset } from '@/api/assets'
import { agentApi } from '@/api/agent'
import { collectionsApi, type BackendCollection } from '@/api/collections'
import type { Asset, AssetVersion, Collection, SearchResult } from '@/types'

// ===== 后端数据 → 前端 Asset 映射 =====
function mapAsset(b: BackendAsset): Asset {
  const ext = b.mime_type.split('/')[1]?.toUpperCase() || 'UNKNOWN'
  const sizeMB = b.file_size / 1024 / 1024
  const va = (b as any).vision_analysis
  return {
    id: b.id,
    name: b.name,
    desc: b.description || '',
    source: b.source || '',
    author: b.uploaded_by,
    date: b.created_at?.substring(0, 10) || '',
    size: sizeMB >= 1 ? sizeMB.toFixed(1) + ' MB' : (b.file_size / 1024).toFixed(0) + ' KB',
    format: ext,
    thumb: (b as any).file_url || b.download_url,
    tags: b.tags || [],
    versions: b.versions || [],
    downloadUrl: b.download_url,
    visionAnalysis: va ? {
      provider: va.provider,
      status: va.status,
      model_name: va.model_name,
      prompt: va.prompt,
      summary: va.summary,
      keywords: va.keywords,
    } : undefined,
  }
}

// ===== Store =====
export const useAssetStore = defineStore('assets', () => {
  // ---- 素材数据（从 API 加载） ----
  const allAssets = ref<Asset[]>([])
  const totalCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ---- 标签 & 分组 ----
  const allTags = ref<string[]>([])
  const collections = ref<Collection[]>([])

  // ---- 筛选 & 分页 ----
  const selectedTags = ref<string[]>([])
  const globalSearch = ref('')
  const pageSize = 24
  const currentPage = ref(1)

  // ---- 搜索 ----
  const searchResults = ref<SearchResult[]>([])
  const searchQuery = ref('')
  const searching = ref(false)
  const searchReasoning = ref('')

  // ---- 计算属性 ----
  const filteredAssets = computed(() => {
    let arr = allAssets.value
    if (selectedTags.value.length > 0) {
      arr = arr.filter(a => selectedTags.value.some(t => a.tags.includes(t)))
    }
    if (globalSearch.value) {
      const q = globalSearch.value.toLowerCase()
      arr = arr.filter(a => a.name.toLowerCase().includes(q) || a.desc.toLowerCase().includes(q))
    }
    return arr
  })

  const pagedAssets = computed(() => {
    const start = (currentPage.value - 1) * pageSize
    return filteredAssets.value.slice(start, start + pageSize)
  })

  const monthNewCount = computed(() => {
    const now = new Date()
    return allAssets.value.filter(a => {
      const d = new Date(a.date)
      return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
    }).length
  })

  const visionReadyCount = computed(() => allAssets.value.filter(a => a.visionAnalysis?.status === 'ready').length)

  // ===== ★ API 方法 =====

  /** 加载素材列表 */
  async function fetchAssets(params?: { page?: number; page_size?: number; query?: string }) {
    loading.value = true
    error.value = null
    try {
      const res = await assetsApi.getAssets({
        page: params?.page || 1,
        page_size: params?.page_size || 100, // 一次加载较多，前端做客户端分页
        query: params?.query || undefined,
      })
      allAssets.value = res.data.items.map(mapAsset)
      totalCount.value = res.data.total
    } catch (e: any) {
      error.value = e?.response?.data?.error?.message || e?.message || '加载素材失败'
    } finally {
      loading.value = false
    }
  }

  /** 获取单个素材 */
  async function fetchAssetById(id: number): Promise<Asset | undefined> {
    try {
      const res = await assetsApi.getAsset(id)
      return mapAsset(res.data)
    } catch {
      // 网络失败时尝试从本地缓存查找
      return allAssets.value.find(a => a.id === id)
    }
  }

  /** 从本地缓存获取（同步，用于快速访问） */
  function getAssetById(id: number): Asset | undefined {
    return allAssets.value.find(a => a.id === id)
  }

  /** 更新素材 */
  async function updateAsset(id: number, data: { name?: string; desc?: string; source?: string }) {
    const res = await assetsApi.updateAsset(id, {
      name: data.name,
      description: data.desc,
      source: data.source,
    })
    const updated = mapAsset(res.data)
    const idx = allAssets.value.findIndex(a => a.id === id)
    if (idx >= 0) allAssets.value[idx] = updated
  }

  /** 删除素材 */
  async function deleteAsset(id: number) {
    await assetsApi.deleteAsset(id)
    allAssets.value = allAssets.value.filter(a => a.id !== id)
    // 清理分组关联
    collections.value.forEach(c => {
      c.asset_count = Math.max(0, c.asset_count - 1)
      if (c.assets) c.assets = c.assets.filter(a => a.id !== id)
    })
  }

  /** 上传素材（在上传视图中调用） */
  async function uploadAsset(formData: FormData, onProgress?: (e: ProgressEvent) => void) {
    const res = await assetsApi.uploadAsset(formData, onProgress)
    const asset = mapAsset(res.data)
    allAssets.value.unshift(asset)
    return asset
  }

  function addAssetTag(assetId: number, tag: string) {
    const a = allAssets.value.find(x => x.id === assetId)
    if (a && !a.tags.includes(tag)) {
      a.tags = [...a.tags, tag]
      if (!allTags.value.includes(tag)) allTags.value.push(tag)
    }
  }

  function removeAssetTag(assetId: number, tag: string) {
    const a = allAssets.value.find(x => x.id === assetId)
    if (a) a.tags = a.tags.filter(t => t !== tag)
  }

  function addVersion(assetId: number, version: AssetVersion) {
    const a = allAssets.value.find(x => x.id === assetId)
    if (a) a.versions = [...a.versions, version]
  }

  function toggleTag(tag: string) {
    const i = selectedTags.value.indexOf(tag)
    i >= 0 ? selectedTags.value.splice(i, 1) : selectedTags.value.push(tag)
    currentPage.value = 1
  }

  function clearFilters() {
    selectedTags.value = []
    globalSearch.value = ''
    currentPage.value = 1
  }

  // ---- 分组管理（对接后端 API） ----

  const collectionsLoading = ref(false)

  function _mapCollection(b: BackendCollection): Collection {
    return {
      id: b.id,
      name: b.name,
      description: b.description || '',
      asset_count: b.asset_count,
      creator: b.creator,
      created_at: b.created_at,
    }
  }

  /** 从后端加载分组列表 */
  async function fetchCollections() {
    collectionsLoading.value = true
    try {
      const res = await collectionsApi.list()
      collections.value = res.data.map(_mapCollection)
    } catch {
      // 静默失败，保留旧数据
    } finally {
      collectionsLoading.value = false
    }
  }

  function getCollectionById(id: number): Collection | undefined {
    return collections.value.find(c => c.id === id)
  }

  function getCollectionAssets(col: Collection): Asset[] {
    return col.assets || []
  }

  /** 创建分组 */
  async function createCollection(name: string, description: string) {
    const res = await collectionsApi.create({ name, description })
    collections.value.push(_mapCollection(res.data))
    return res.data.id
  }

  /** 添加素材到分组 */
  async function addToCollection(collectionId: number, assetId: number) {
    await collectionsApi.addAsset(collectionId, assetId)
    const c = collections.value.find(x => x.id === collectionId)
    if (c) c.asset_count += 1
  }

  /** 从分组移除素材 */
  async function removeFromCollection(collectionId: number, assetId: number) {
    await collectionsApi.removeAsset(collectionId, assetId)
    const c = collections.value.find(x => x.id === collectionId)
    if (c) {
      c.asset_count = Math.max(0, c.asset_count - 1)
      if (c.assets) c.assets = c.assets.filter(a => a.id !== assetId)
    }
  }

  /** 删除分组 */
  async function deleteCollection(id: number) {
    await collectionsApi.delete(id)
    collections.value = collections.value.filter(c => c.id !== id)
  }

  // Agent 语义搜索（调用 POST /api/v1/agent/search）
  async function doSearch(query: string) {
    if (!query.trim()) return
    searchQuery.value = query
    searching.value = true
    searchReasoning.value = ''
    try {
      const res = await agentApi.search({ query, page: 1, page_size: 50 })
      searchResults.value = res.data.items.map(item => ({
        ...mapAsset(item.asset),
        score: Math.round((item.llm_relevance ?? item.score) * 100),
        matchReasons: item.match_reasons || [],
      }))
      searchReasoning.value = res.data.reasoning || ''
    } catch (e: any) {
      ElMessage.error('搜索失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
      searchResults.value = []
      searchReasoning.value = ''
    } finally {
      searching.value = false
    }
  }

  return {
    allAssets, totalCount, loading, error, allTags, collections, collectionsLoading,
    selectedTags, globalSearch, pageSize, currentPage,
    searchResults, searchQuery, searching, searchReasoning,
    filteredAssets, pagedAssets, monthNewCount, visionReadyCount,
    fetchAssets, fetchAssetById, getAssetById, updateAsset, deleteAsset, uploadAsset,
    addAssetTag, removeAssetTag, addVersion, toggleTag, clearFilters,
    fetchCollections, getCollectionById, getCollectionAssets, createCollection, addToCollection, removeFromCollection, deleteCollection,
    doSearch,
  }
})
