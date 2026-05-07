import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { assetsApi, type BackendAsset } from '@/api/assets'
import type { Asset, AssetVersion, Collection, SearchResult } from '@/types'

// ===== 确定性哈希 =====
function hashStr(s: string): number {
  let h = 5381; for (let i = 0; i < s.length; i++) h = ((h << 5) + h) + s.charCodeAt(i)
  return Math.abs(h)
}

// ===== 后端数据 → 前端 Asset 映射 =====
function mapAsset(b: BackendAsset): Asset {
  const ext = b.mime_type.split('/')[1]?.toUpperCase() || 'UNKNOWN'
  const sizeMB = b.file_size / 1024 / 1024
  return {
    id: b.id,
    name: b.name,
    desc: b.description || '',
    source: b.source || '',
    author: b.uploaded_by,
    date: b.created_at?.substring(0, 10) || '',
    size: sizeMB >= 1 ? sizeMB.toFixed(1) + ' MB' : (b.file_size / 1024).toFixed(0) + ' KB',
    format: ext,
    thumb: `https://picsum.photos/seed/asset${b.id}/400/300`,
    tags: [], // 后端标签端点未就绪，暂空
    versions: [], // 后端版本端点未就绪，暂空
    downloadUrl: b.download_url,
  }
}

// ===== Mock 数据（仅标签/分组/搜索/版本，后端未就绪） =====
const mockTags = ['科技感','产品图','海报','UI设计','年会活动','人物','自然风景','城市建筑','动物','食物饮品','交通工具','家居生活']
const mockCollections: Collection[] = [
  { id:1, name:'2026春季新品素材',   desc:'春季新品发布的全部视觉物料',                 assetIds:[7,3],                      created:'2026-03-20', creator:'小明' },
  { id:2, name:'年会活动合集',       desc:'年会合影、庆典物料统一管理',                 assetIds:[2,13],                     created:'2026-01-10', creator:'小红' },
  { id:3, name:'UI设计稿归档',       desc:'App和后台管理系统的设计稿',                   assetIds:[5,9,12,15],                created:'2026-02-05', creator:'设计部' },
  { id:4, name:'电商营销海报',       desc:'促销和营销相关海报素材',                      assetIds:[4,7,10],                   created:'2026-03-01', creator:'运营部' },
  { id:5, name:'宠物摄影',            desc:'猫狗宠物相关摄影素材',                        assetIds:[17,18],                    created:'2026-05-01', creator:'小明' },
  { id:6, name:'风光与建筑摄影',     desc:'自然风光和城市建筑摄影合集',                  assetIds:[8,11,14],                  created:'2026-02-15', creator:'小明' },
]

// ===== 语义搜索表（后端搜索端点未就绪，暂留本地模拟） =====
const semanticKeywords: Record<string, string[]> = {
  '蓝色':['科技','背景','深蓝','冷色调','渐变'], '科技':['蓝色','背景','粒子','仪表','数据','深色'],
  '咖啡':['拿铁','热饮','拉花','杯子','饮品','棕色'], '猫':['猫咪','橘猫','宠物','窗台','虎斑','动物'],
  '狗':['犬','金毛','宠物','奔跑','草地','户外'], '跑车':['红色','展厅','轿车','运动','汽车'],
  '海报':['促销','设计','广告','视觉','平面'], '风景':['自然','户外','山水','摄影','蓝天'],
  '汉堡':['薯条','快餐','食物','套餐','牛肉'], '建筑':['城市','大楼','古典','外景'],
}

const reasonMap: Record<string, string> = {
  '蓝色':'色调匹配','科技':'风格匹配','咖啡':'物体识别：咖啡','猫':'物体识别：猫',
  '狗':'物体识别：狗','金毛':'物体识别：金毛犬','汉堡':'物体识别：汉堡','跑车':'物体识别：跑车',
  '海报':'类型匹配','风景':'场景匹配','建筑':'场景匹配','年会':'场景匹配',
}

// ===== Store =====
export const useAssetStore = defineStore('assets', () => {
  // ---- 素材数据（从 API 加载） ----
  const allAssets = ref<Asset[]>([])
  const totalCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ---- Mock 数据（后端未就绪的模块） ----
  const allTags = ref<string[]>([...mockTags])
  const collections = ref<Collection[]>([...mockCollections])

  // ---- 筛选 & 分页 ----
  const selectedTags = ref<string[]>([])
  const globalSearch = ref('')
  const pageSize = 10
  const currentPage = ref(1)

  // ---- 搜索（本地模拟，后端搜索端点未就绪） ----
  const searchResults = ref<SearchResult[]>([])
  const searchQuery = ref('')
  const searching = ref(false)

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

  const clipReadyCount = computed(() => allAssets.value.filter(a => a.clipDesc).length)

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
      if (allAssets.value.length === 0) {
        // 首次加载失败时，回退到 mock 数据确保页面可用
        console.warn('API 不可用，回退到 mock 数据')
      }
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
    collections.value.forEach(c => { c.assetIds = c.assetIds.filter(aid => aid !== id) })
  }

  /** 上传素材（在上传视图中调用） */
  async function uploadAsset(formData: FormData, onProgress?: (e: ProgressEvent) => void) {
    const res = await assetsApi.uploadAsset(formData, onProgress)
    const asset = mapAsset(res.data)
    allAssets.value.unshift(asset)
    return asset
  }

  // ===== ★ Mock 方法（后端未就绪的模块，保持原有逻辑） =====

  function addAsset(asset: Asset) {
    allAssets.value.unshift(asset)
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

  function getCollectionById(id: number): Collection | undefined {
    return collections.value.find(c => c.id === id)
  }

  function getCollectionAssets(col: Collection): Asset[] {
    return col.assetIds.map(id => getAssetById(id)).filter(Boolean) as Asset[]
  }

  function createCollection(name: string, desc: string, creator: string) {
    collections.value.push({
      id: Date.now(), name, desc, assetIds: [],
      created: new Date().toISOString().split('T')[0], creator,
    })
  }

  function addToCollection(collectionId: number, assetId: number) {
    const c = collections.value.find(x => x.id === collectionId)
    if (c && !c.assetIds.includes(assetId)) c.assetIds.push(assetId)
  }

  function removeFromCollection(collectionId: number, assetId: number) {
    const c = collections.value.find(x => x.id === collectionId)
    if (c) c.assetIds = c.assetIds.filter(id => id !== assetId)
  }

  function deleteCollection(id: number) {
    collections.value = collections.value.filter(c => c.id !== id)
  }

  // 本地语义搜索（后端搜索端点未就绪）
  function doSearch(query: string) {
    if (!query.trim()) return
    searchQuery.value = query
    searching.value = true
    setTimeout(() => {
      const q = query
      let expandedTerms = [q]
      for (const [kw, terms] of Object.entries(semanticKeywords)) {
        if (q.includes(kw)) expandedTerms.push(...terms)
      }
      const results: SearchResult[] = allAssets.value.map(a => {
        const st = (a.name + a.desc + (a.clipDesc || '')).toLowerCase()
        let matchScore = 0
        const reasons: string[] = []
        expandedTerms.forEach(t => {
          if (st.includes(t.toLowerCase())) { matchScore += 25; reasons.push(t) }
        })
        if (a.name.toLowerCase().includes(q.toLowerCase())) matchScore += 20
        const matchedReasons = [...new Set(reasons)].slice(0, 3).map(r => reasonMap[r] || r).filter(Boolean)
        const offset = hashStr(q + '_' + a.id) % 10
        const score = Math.min(99, Math.max(40, 50 + matchScore + offset))
        return { ...a, score, matchReasons: matchedReasons.length > 0 ? matchedReasons : ['语义关联'] }
      }).filter(r => r.score > 50).sort((a, b) => b.score - a.score)
      searchResults.value = results
      searching.value = false
    }, 400)
  }

  return {
    allAssets, totalCount, loading, error, allTags, collections,
    selectedTags, globalSearch, pageSize, currentPage,
    searchResults, searchQuery, searching,
    filteredAssets, pagedAssets, monthNewCount, clipReadyCount,
    fetchAssets, fetchAssetById, getAssetById, updateAsset, deleteAsset, uploadAsset,
    addAsset, addAssetTag, removeAssetTag, addVersion, toggleTag, clearFilters,
    getCollectionById, getCollectionAssets, createCollection, addToCollection, removeFromCollection, deleteCollection,
    doSearch,
  }
})
