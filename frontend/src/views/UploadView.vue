<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAssetStore } from '@/stores/assets'
import { ElMessage } from 'element-plus'
import { visionApi, type VisionAnalyzeResponse } from '@/api/vision'

const auth = useAuthStore()
const store = useAssetStore()

// ---- 步骤控制 ----
type Step = 'select' | 'analyze' | 'upload'
const currentStep = ref<Step>('select')
const uploadSteps: Array<{ key: Step; label: string; desc: string }> = [
  { key: 'select', label: '选择图片', desc: '点击或拖拽选择文件' },
  { key: 'analyze', label: 'AI 图片分析', desc: '自动识别内容并填写信息' },
  { key: 'upload', label: '确认上传', desc: '检查信息后提交入库' },
]

// ---- 模式：single（选图片）或 zip（选 ZIP 包） ----
type UploadMode = 'single' | 'zip'
const uploadMode = ref<UploadMode>('single')

// ---- 文件 ----
const dragOver = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const zipInput = ref<HTMLInputElement | null>(null)

// ---- 单张模式：每图独立分析 ----
interface SingleEntry {
  name: string
  preview: string
  file: File
  analyzed: boolean
  analyzing: boolean
  provider: string
  model: string
  model_version: string
  prompt: string
  summary: string
  keywords: string[]
  editedPrompt: string
  editedKeywords: string[]
  editError: string
}
const singleEntries = ref<SingleEntry[]>([])
const activeIndex = ref(0)

function makeEmptyEntry(f: { name: string; preview: string; file: File }): SingleEntry {
  return {
    name: f.name, preview: f.preview, file: f.file,
    analyzed: false, analyzing: false,
    provider: '', model: '', model_version: '',
    prompt: '', summary: '', keywords: [],
    editedPrompt: '', editedKeywords: [],
    editError: '',
  }
}

// ---- 当前活跃图片的 computed 别名（模板中方便使用） ----
const activeEntry = computed(() => singleEntries.value[activeIndex.value])
const hasAnyAnalyzed = computed(() => singleEntries.value.some(e => e.analyzed))

// ---- 全局来源 ----
const formSource = ref('')

// ===== 草稿持久化（localStorage + IndexedDB） =====
const DRAFT_KEY = 'upload_draft_meta'
const DB_NAME = 'upload_drafts'
const DB_VERSION = 1

function openFileDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open(DB_NAME, DB_VERSION)
    r.onupgradeneeded = () => { r.result.createObjectStore('files', { keyPath: 'name' }) }
    r.onsuccess = () => resolve(r.result)
    r.onerror = () => reject(r.error)
  })
}

async function storeFileToDB(file: File) {
  const db = await openFileDB()
  const tx = db.transaction('files', 'readwrite')
  tx.objectStore('files').put({ name: file.name, file, ts: Date.now() })
}

async function getFileFromDB(name: string): Promise<File | undefined> {
  const db = await openFileDB()
  return new Promise((resolve) => {
    const tx = db.transaction('files', 'readonly')
    const req = tx.objectStore('files').get(name)
    req.onsuccess = () => resolve(req.result?.file)
    req.onerror = () => resolve(undefined)
  })
}

async function clearFileDB() {
  const db = await openFileDB()
  const tx = db.transaction('files', 'readwrite')
  tx.objectStore('files').clear()
}

async function generateThumbnail(file: File): Promise<string> {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const maxW = 200
      const scale = maxW / img.width
      canvas.width = maxW
      canvas.height = Math.round(img.height * scale)
      canvas.getContext('2d')!.drawImage(img, 0, 0, canvas.width, canvas.height)
      resolve(canvas.toDataURL('image/jpeg', 0.5))
    }
    img.src = URL.createObjectURL(file)
  })
}

type DraftEntry = {
  name: string; thumb: string
  analyzed: boolean
  provider: string; model: string; model_version: string
  prompt: string; summary: string; keywords: string[]
  editedPrompt: string; editedKeywords: string[]
}
type DraftData = { mode: UploadMode; source: string; singleEntries: DraftEntry[]; activeIndex: number }

async function saveDraft() {
  if (singleEntries.value.length === 0) return
  const entries: DraftEntry[] = await Promise.all(
    singleEntries.value.map(async e => ({
      name: e.name, thumb: await generateThumbnail(e.file),
      analyzed: e.analyzed, provider: e.provider, model: e.model, model_version: e.model_version,
      prompt: e.prompt, summary: e.summary, keywords: e.keywords,
      editedPrompt: e.editedPrompt, editedKeywords: e.editedKeywords,
    }))
  )
  const data: DraftData = { mode: uploadMode.value, source: formSource.value, singleEntries: entries, activeIndex: activeIndex.value }
  localStorage.setItem(DRAFT_KEY, JSON.stringify(data))
  // 同时存文件到 IndexedDB
  for (const e of singleEntries.value) {
    try { await storeFileToDB(e.file) } catch (_) { /* ignore */ }
  }
}

async function loadDraft(): Promise<boolean> {
  const raw = localStorage.getItem(DRAFT_KEY)
  if (!raw) return false
  let data: DraftData
  try { data = JSON.parse(raw) } catch { return false }
  if (!data.singleEntries || data.singleEntries.length === 0) return false

  // 尝试从 IndexedDB 恢复文件
  const restored: SingleEntry[] = []
  let anyFileRestored = false
  for (const de of data.singleEntries) {
    const file = await getFileFromDB(de.name)
    const entry = makeEmptyEntry({ name: de.name, preview: de.thumb, file: file || new File([], de.name) })
    if (file) anyFileRestored = true
    entry.analyzed = de.analyzed
    entry.provider = de.provider; entry.model = de.model; entry.model_version = de.model_version
    entry.prompt = de.prompt; entry.summary = de.summary; entry.keywords = de.keywords || []
    entry.editedPrompt = de.editedPrompt; entry.editedKeywords = de.editedKeywords || []
    restored.push(entry)
  }

  singleEntries.value = restored
  formSource.value = data.source || ''
  uploadMode.value = data.mode || 'single'
  activeIndex.value = data.activeIndex || 0

  if (anyFileRestored && restored.some(e => e.analyzed)) {
    currentStep.value = 'upload'
    ElMessage.info(`已恢复 ${restored.length} 个草稿`)
  } else if (anyFileRestored) {
    currentStep.value = 'select'
    ElMessage.info(`已恢复 ${restored.length} 个文件，请重新分析`)
  } else {
    currentStep.value = 'select'
    ElMessage.warning(`草稿文件数据已过期，请重新选择图片。分析结果已保留为参考。`)
  }
  return true
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY)
  clearFileDB().catch(() => {})
}

// 分析完成后自动保存
watch(
  () => singleEntries.value.filter(e => e.analyzed).length,
  () => { saveDraft().catch(() => {}) },
)
// 编辑时防抖保存
let saveTimer: ReturnType<typeof setTimeout>
watch(
  () => singleEntries.value.map(e => ({ p: e.editedPrompt, k: e.editedKeywords })),
  () => { clearTimeout(saveTimer); saveTimer = setTimeout(() => saveDraft().catch(() => {}), 1500) },
  { deep: true },
)
// 来源变化保存
watch(formSource, () => { clearTimeout(saveTimer); saveTimer = setTimeout(() => saveDraft().catch(() => {}), 1500) })

onMounted(() => { loadDraft() })

// ---- ZIP 批量分析 ----
interface ZipEntryResult {
  name: string
  file: File
  preview: string
  status: 'pending' | 'analyzing' | 'done' | 'error'
  analysis: VisionAnalyzeResponse | null
  editedPrompt: string
  editedKeywords: string[]
  errorMsg: string
}
const zipResults = ref<ZipEntryResult[]>([])
const zipAnalyzing = ref(false)
const zipAnalyzeProgress = ref({ current: 0, total: 0 })

// ---- 上传 ----
const uploading = ref(false)
const uploadProgress = ref<Record<string, number>>({})

// ===== 文件操作 =====
function triggerUpload() {
  if (!auth.isGuest) fileInput.value?.click()
}
function triggerZipUpload() {
  if (!auth.isGuest) zipInput.value?.click()
}
function onFileSelect(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files) addFiles(Array.from(files))
}
function onZipSelect(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files && files.length > 0) handleZipFile(files[0])
}
function onDrop(e: DragEvent) {
  dragOver.value = false
  const files = e.dataTransfer?.files
  if (!files) return
  const fileList = Array.from(files)
  const imageFiles = fileList.filter(f => f.type.startsWith('image/'))
  const zipFiles = fileList.filter(f => f.name.endsWith('.zip') || f.type === 'application/zip')

  if (zipFiles.length > 0) {
    handleZipFile(zipFiles[0])
    if (imageFiles.length > 0) addFiles(imageFiles)
  } else if (imageFiles.length > 0) {
    addFiles(imageFiles)
  }
}

function addFiles(files: File[]) {
  uploadMode.value = 'single'
  const newEntries: SingleEntry[] = []
  files.forEach(f => {
    if (!singleEntries.value.find(x => x.name === f.name)) {
      newEntries.push(makeEmptyEntry({ name: f.name, preview: URL.createObjectURL(f), file: f }))
    }
  })
  if (newEntries.length > 0) {
    singleEntries.value = [...singleEntries.value, ...newEntries]
    activeIndex.value = singleEntries.value.length - newEntries.length
  }
  currentStep.value = 'select'
}

function removeFile(idx: number) {
  singleEntries.value.splice(idx, 1)
  if (activeIndex.value >= singleEntries.value.length) {
    activeIndex.value = Math.max(0, singleEntries.value.length - 1)
  }
}

function selectImage(idx: number) {
  activeIndex.value = idx
  // 如果已分析过或正在分析，进入对应的步骤状态
  if (singleEntries.value[idx].analyzed) {
    currentStep.value = 'upload'
  } else if (!singleEntries.value[idx].analyzing) {
    currentStep.value = 'select'
  }
}

const hasFiles = computed(() => singleEntries.value.length > 0)
const hasZipEntries = computed(() => zipResults.value.length > 0)

// ===== ZIP 处理 =====
async function handleZipFile(zipFile: File) {
  zipResults.value = []
  zipAnalyzing.value = true
  uploadMode.value = 'zip'
  currentStep.value = 'select'

  try {
    const JSZip = (await import('jszip')).default
    const zip = await JSZip.loadAsync(zipFile)
    const imageExts = ['.jpg', '.jpeg', '.png', '.webp']
    const entries: { name: string; file: File; preview: string }[] = []

    for (const [filename, zipEntry] of Object.entries(zip.files)) {
      if (zipEntry.dir) continue
      const ext = '.' + filename.split('.').pop()?.toLowerCase()
      if (!imageExts.includes(ext)) continue
      const blob = await zipEntry.async('blob')
      const mimeMap: Record<string, string> = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' }
      const file = new File([blob], filename.split('/').pop() || filename, { type: mimeMap[ext] || 'image/jpeg' })
      entries.push({ name: file.name, file, preview: URL.createObjectURL(file) })
    }

    if (entries.length === 0) {
      ElMessage.warning('ZIP 文件中未找到图片文件')
      return
    }

    zipResults.value = entries.map(e => ({
      ...e,
      status: 'pending' as const,
      analysis: null,
      editedPrompt: '',
      editedKeywords: [] as string[],
      errorMsg: '',
    }))

    ElMessage.success(`从 ZIP 中提取了 ${entries.length} 张图片`)
  } catch (e: any) {
    ElMessage.error('ZIP 解压失败：' + (e?.message || '未知错误'))
  } finally {
    zipAnalyzing.value = false
  }
}

async function runZipAnalysis() {
  if (zipResults.value.length === 0) return
  zipAnalyzeProgress.value = { current: 0, total: zipResults.value.length }
  currentStep.value = 'analyze'

  for (const entry of zipResults.value) {
    entry.status = 'analyzing'
    try {
      const fd = new FormData()
      fd.append('file', entry.file)
      const res = await visionApi.analyze(fd)
      entry.analysis = res.data
      entry.editedPrompt = res.data.prompt
      entry.editedKeywords = [...res.data.keywords]
      entry.status = 'done'
    } catch (e: any) {
      entry.status = 'error'
      entry.errorMsg = e?.response?.data?.detail || e?.message || '分析失败'
    }
    zipAnalyzeProgress.value.current++
  }

  const doneCount = zipResults.value.filter(r => r.status === 'done').length
  const errCount = zipResults.value.filter(r => r.status === 'error').length
  if (errCount === 0) {
    ElMessage.success(`全部 ${doneCount} 张图片分析完成`)
  } else {
    ElMessage.warning(`${doneCount} 张成功，${errCount} 张失败`)
  }

  const allDone = zipResults.value.every(r => r.status === 'done' || r.status === 'error')
  if (allDone) currentStep.value = 'upload'
}

// ===== 步骤 2：AI 图片分析（单张模式——分析当前活跃图片） =====
async function runAnalysis() {
  const entry = activeEntry.value
  if (!entry) return
  entry.analyzing = true
  entry.editError = ''
  currentStep.value = 'analyze'

  try {
    const fd = new FormData()
    fd.append('file', entry.file)

    const res = await visionApi.analyze(fd)
    const data = res.data

    entry.provider = data.provider
    entry.model = data.model
    entry.model_version = data.model_version
    entry.prompt = data.prompt
    entry.summary = data.summary
    entry.keywords = data.keywords
    entry.editedPrompt = data.prompt
    entry.editedKeywords = [...data.keywords]
    entry.analyzed = true

    currentStep.value = 'upload'
  } catch (e: any) {
    entry.editError = e?.response?.data?.detail || e?.message || '分析失败'
    ElMessage.error('AI 分析失败：' + entry.editError)
  } finally {
    entry.analyzing = false
  }
}

// ===== 分析所有未分析的图片 =====
async function runAnalysisAll() {
  const pending = singleEntries.value.filter(e => !e.analyzed)
  if (pending.length === 0) return
  currentStep.value = 'analyze'

  let doneCount = 0
  let failCount = 0
  for (const entry of pending) {
    entry.analyzing = true
    entry.editError = ''
    try {
      const fd = new FormData()
      fd.append('file', entry.file)
      const res = await visionApi.analyze(fd)
      entry.provider = res.data.provider
      entry.model = res.data.model
      entry.model_version = res.data.model_version
      entry.prompt = res.data.prompt
      entry.summary = res.data.summary
      entry.keywords = res.data.keywords
      entry.editedPrompt = res.data.prompt
      entry.editedKeywords = [...res.data.keywords]
      entry.analyzed = true
      doneCount++
    } catch (e: any) {
      entry.editError = e?.response?.data?.detail || e?.message || '分析失败'
      failCount++
    } finally {
      entry.analyzing = false
    }
  }

  if (failCount === 0) {
    ElMessage.success(`全部 ${doneCount} 张图片分析完成`)
  } else {
    ElMessage.warning(`${doneCount} 张成功，${failCount} 张失败`)
  }
  currentStep.value = 'upload'
}

const analyzingAny = computed(() => singleEntries.value.some(e => e.analyzing))

// ===== 步骤 3：确认并上传 =====
async function confirmAndUpload() {
  uploading.value = true
  let successCount = 0
  let failCount = 0

  if (uploadMode.value === 'zip') {
    for (const entry of zipResults.value) {
      if (entry.status === 'error') { failCount++; continue }
      uploadProgress.value[entry.name] = 0
      try {
        const fd = new FormData()
        fd.append('file', entry.file)
        fd.append('name', entry.name.replace(/\.[^.]+$/, ''))
        fd.append('description', entry.editedPrompt)
        if (entry.editedKeywords.length > 0) fd.append('tags', JSON.stringify(entry.editedKeywords))
        fd.append('source', formSource.value)
        // 传递前端 AI 分析结果，避免后端重复调用 Qwen3-VL
        if (entry.analysis?.prompt) {
          fd.append('prompt', entry.analysis.prompt)
          fd.append('summary', entry.analysis.summary || '')
          fd.append('keywords', JSON.stringify(entry.analysis.keywords))
        }

        await store.uploadAsset(fd, (e: ProgressEvent) => {
          if (e.total) uploadProgress.value[entry.name] = Math.round((e.loaded / e.total) * 100)
        })
        uploadProgress.value[entry.name] = 100
        successCount++
      } catch (e: any) {
        uploadProgress.value[entry.name] = -1
        failCount++
        ElMessage.error(`${entry.name} 上传失败：${e?.response?.data?.error?.message || e?.message || '未知错误'}`)
      }
    }
  } else {
    // 单张模式：每张图用各自的可复现提示词和关键词
    for (const entry of singleEntries.value) {
      uploadProgress.value[entry.name] = 0
      try {
        const fd = new FormData()
        fd.append('file', entry.file)
        fd.append('name', entry.name.replace(/\.[^.]+$/, ''))
        fd.append('description', entry.editedPrompt)
        if (entry.editedKeywords.length > 0) fd.append('tags', JSON.stringify(entry.editedKeywords))
        fd.append('source', formSource.value)
        // 传递前端 AI 分析结果，避免后端重复调用 Qwen3-VL
        if (entry.analyzed && entry.prompt) {
          fd.append('prompt', entry.prompt)
          fd.append('summary', entry.summary)
          fd.append('keywords', JSON.stringify(entry.keywords))
        }

        await store.uploadAsset(fd, (e: ProgressEvent) => {
          if (e.total) uploadProgress.value[entry.name] = Math.round((e.loaded / e.total) * 100)
        })
        uploadProgress.value[entry.name] = 100
        successCount++
      } catch (e: any) {
        uploadProgress.value[entry.name] = -1
        failCount++
        ElMessage.error(`${entry.name} 上传失败：${e?.response?.data?.error?.message || e?.message || '未知错误'}`)
      }
    }
  }

  uploading.value = false

  if (failCount === 0) {
    ElMessage.success(`全部 ${successCount} 个文件上传完成`)
    clearDraft()
    singleEntries.value = []
    zipResults.value = []
    formSource.value = ''
    currentStep.value = 'select'
    uploadMode.value = 'single'
  } else if (successCount > 0) {
    ElMessage.warning(`${successCount} 个成功，${failCount} 个失败`)
  }
}

// ===== 切换回单张模式 =====
function switchToSingle() {
  uploadMode.value = 'single'
  zipResults.value = []
  singleEntries.value = []
  formSource.value = ''
  currentStep.value = 'select'
  clearDraft()
}

// ===== 步骤状态 =====
const stepStatus = computed(() => ({
  select: currentStep.value === 'select' ? 'active' : (currentStep.value === 'analyze' || currentStep.value === 'upload') ? 'done' : 'pending',
  analyze: currentStep.value === 'analyze' ? 'active' : currentStep.value === 'upload' ? 'done' : 'pending',
  upload: currentStep.value === 'upload' ? 'active' : 'pending',
}))
</script>

<template>
  <div class="upload-page">
  <el-alert v-if="auth.isGuest" title="访客无法上传，请先登录编辑或管理员账号" type="warning" show-icon :closable="false" style="margin-bottom:20px" />

  <!-- ===== 步骤指示器 ===== -->
  <div class="upload-steps" style="display:flex;gap:16px;margin-bottom:20px">
    <div v-for="(step, i) in uploadSteps" :key="step.key"
      class="upload-step-card"
      style="flex:1;background:#fff;border-radius:8px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,0.06);display:flex;align-items:center;gap:12px"
      :style="{ opacity: currentStep === step.key ? 1 : stepStatus[step.key] === 'done' ? 0.85 : 0.5 }"
    >
      <span style="width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0;color:#fff"
        :style="{ background: stepStatus[step.key] === 'done' ? '#67C23A' : stepStatus[step.key] === 'active' ? '#7C3AED' : '#c0c4cc' }">
        {{ stepStatus[step.key] === 'done' ? '✓' : i + 1 }}
      </span>
      <div>
        <b style="font-size:14px;color:#303133">{{ step.label }}</b>
        <div style="font-size:12px;color:#909399">{{ step.desc }}</div>
      </div>
    </div>
  </div>

  <!-- ===== 步骤 1：选择文件 ===== -->

  <!-- 单张模式上传区 -->
  <div v-if="uploadMode !== 'zip'" :class="['upload-zone', { dragover: dragOver }]"
    @click="triggerUpload" @dragover.prevent="dragOver=true" @dragleave="dragOver=false" @drop.prevent="onDrop">
    <div class="zone-icon"><el-icon><UploadFilled /></el-icon></div>
    <p style="font-size:16px;font-weight:600;color:#303133">点击或拖拽图片到此区域</p>
    <p class="sub">支持 JPG / PNG / WebP，单文件 ≤20MB。也可拖入 .zip 批量上传</p>
    <input type="file" ref="fileInput" multiple accept="image/jpeg,image/png,image/webp" style="display:none" @change="onFileSelect">
  </div>

  <!-- ZIP 模式上传区 -->
  <div v-else :class="['upload-zone', { dragover: dragOver }]"
    @click="triggerZipUpload" @dragover.prevent="dragOver=true" @dragleave="dragOver=false" @drop.prevent="onDrop">
    <div class="zone-icon"><el-icon><FolderOpened /></el-icon></div>
    <p style="font-size:16px;font-weight:600;color:#303133">点击或拖拽 .zip 压缩包到此区域</p>
    <p class="sub">自动解压提取图片，逐张 AI 分析后批量上传</p>
    <input type="file" ref="zipInput" accept=".zip" style="display:none" @change="onZipSelect">
    <el-button type="default" style="margin-top:12px" @click.stop="switchToSingle">切换到单张上传模式</el-button>
  </div>

  <!-- ===== 单张模式：缩略图列表（点击切换活跃图片） ===== -->
  <div v-if="hasFiles && uploadMode === 'single'" style="margin-bottom:20px">
    <div class="upload-section-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <span style="font-size:14px;color:#606266">
        已选择 <b>{{ singleEntries.length }}</b> 个文件
        <span v-if="hasAnyAnalyzed" style="color:#67C23A;margin-left:8px">
          · {{ singleEntries.filter(e => e.analyzed).length }} 张已分析
        </span>
      </span>
      <div class="upload-action-row" style="display:flex;gap:8px">
        <el-button
          v-if="currentStep === 'select'"
          type="primary" :icon="Cpu"
          @click="runAnalysis"
        >分析当前图片</el-button>
        <el-button
          v-if="singleEntries.length > 1 && singleEntries.some(e => !e.analyzed)"
          type="primary" plain :icon="Cpu"
          @click="runAnalysisAll"
        >逐张分析全部</el-button>
      </div>
    </div>
    <div class="upload-thumb-list" style="display:flex;gap:8px;flex-wrap:wrap">
      <div v-for="(entry, i) in singleEntries" :key="i"
        @click="selectImage(i)"
        class="upload-thumb-item"
        style="position:relative;width:120px;text-align:center;cursor:pointer;border-radius:8px;padding:6px;transition:all 0.15s"
        :style="{
          background: i === activeIndex ? '#f0ebff' : '#fff',
          boxShadow: i === activeIndex
            ? '0 0 0 2px #7C3AED, 0 1px 4px rgba(0,0,0,0.08)'
            : '0 1px 4px rgba(0,0,0,0.06)',
        }"
      >
        <img :src="entry.preview" style="width:108px;height:81px;object-fit:cover;border-radius:6px">
        <div style="font-size:11px;color:#606266;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ entry.name }}</div>
        <!-- 状态标记 -->
        <span v-if="entry.analyzed" style="position:absolute;top:-2px;right:-2px;width:18px;height:18px;border-radius:50%;background:#67C23A;color:#fff;font-size:11px;display:flex;align-items:center;justify-content:center">✓</span>
        <span v-else-if="entry.analyzing" style="position:absolute;top:-2px;right:-2px;width:18px;height:18px;border-radius:50%;background:#E6A23C;color:#fff;font-size:10px;display:flex;align-items:center;justify-content:center">⏳</span>
        <span v-else-if="entry.editError" style="position:absolute;top:-2px;right:-2px;width:18px;height:18px;border-radius:50%;background:#F56C6C;color:#fff;font-size:11px;display:flex;align-items:center;justify-content:center">!</span>
        <!-- 进度条 -->
        <div v-if="uploadProgress[entry.name] !== undefined && uploadProgress[entry.name] >= 0" style="margin-top:2px">
          <el-progress :percentage="uploadProgress[entry.name]" :stroke-width="3" :status="uploadProgress[entry.name] === 100 ? 'success' : undefined" />
        </div>
        <div v-else-if="uploadProgress[entry.name] === -1" style="margin-top:2px">
          <el-tag type="danger" size="small">失败</el-tag>
        </div>
        <el-button v-if="currentStep === 'select' || currentStep === 'upload'"
          style="position:absolute;top:2px;left:2px"
          size="small" type="danger" circle :icon="Close" plain
          @click.stop="removeFile(i)"
        />
      </div>
    </div>
  </div>

  <!-- ===== ZIP 模式：解压中 ===== -->
  <div v-if="zipAnalyzing" class="analysis-panel">
    <div class="panel-title"><el-icon><FolderOpened /></el-icon>正在解压 ZIP 文件...</div>
    <el-progress :percentage="100" :indeterminate="true" :stroke-width="4" />
  </div>

  <!-- ===== ZIP 模式：图片列表 + 分析 ===== -->
  <div v-if="hasZipEntries && !zipAnalyzing" style="margin-bottom:20px">
    <div class="upload-section-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <span style="font-size:14px;color:#606266">ZIP 包中有 <b>{{ zipResults.length }}</b> 张图片</span>
      <div class="upload-action-row" style="display:flex;gap:8px">
        <el-button
          v-if="currentStep === 'select'"
          type="primary" :icon="Cpu"
          @click="runZipAnalysis"
        >逐张 AI 分析</el-button>
        <el-button type="default" @click="switchToSingle">切换到单张模式</el-button>
      </div>
    </div>

    <!-- ZIP 分析进度 -->
    <div v-if="currentStep === 'analyze' && zipAnalyzeProgress.total > 0" class="analysis-panel" style="margin-bottom:16px">
      <div class="panel-title">
        <el-icon><Cpu /></el-icon>正在逐张分析（{{ zipAnalyzeProgress.current }} / {{ zipAnalyzeProgress.total }}）
      </div>
      <el-progress
        :percentage="Math.round((zipAnalyzeProgress.current / zipAnalyzeProgress.total) * 100)"
        :indeterminate="false" :stroke-width="4"
        style="margin-bottom:8px"
      />
      <span style="font-size:12px;color:#909399">正在调用 Qwen3-VL 分析每张图片...</span>
    </div>

    <!-- ZIP 图片结果表格 -->
    <div class="upload-table-wrap" style="overflow-x:auto;background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="background:#f5f7fa;text-align:left">
            <th style="padding:10px 12px;width:80px">预览</th>
            <th style="padding:10px 12px;width:120px">文件名</th>
            <th style="padding:10px 12px;min-width:200px">可复现提示词</th>
            <th style="padding:10px 12px;min-width:150px">关键词</th>
            <th style="padding:10px 12px;width:70px">状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, idx) in zipResults" :key="idx"
            style="border-top:1px solid #ebeef5"
            :style="{ background: entry.status === 'error' ? '#fef0f0' : '' }"
          >
            <td style="padding:8px 12px">
              <img :src="entry.preview" style="width:60px;height:45px;object-fit:cover;border-radius:4px">
            </td>
            <td style="padding:8px 12px;color:#303133;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ entry.name }}</td>
            <td style="padding:8px 12px">
              <template v-if="entry.status === 'done'">
                <el-input
                  v-model="entry.editedPrompt"
                  size="small"
                  type="textarea"
                  :rows="2"
                  placeholder="AI 生成的可复现提示词"
                />
              </template>
              <template v-else-if="entry.status === 'error'">
                <span style="color:#f56c6c;font-size:12px">{{ entry.errorMsg }}</span>
              </template>
              <template v-else-if="entry.status === 'analyzing'">
                <span style="color:#409eff;font-size:12px">分析中...</span>
              </template>
              <template v-else>
                <span style="color:#c0c4cc;font-size:12px">等待分析</span>
              </template>
            </td>
            <td style="padding:8px 12px">
              <template v-if="entry.status === 'done'">
                <el-select
                  v-model="entry.editedKeywords"
                  multiple
                  size="small"
                  placeholder="关键词"
                  style="width:100%"
                  filterable
                  allow-create
                >
                  <el-option v-for="t in entry.editedKeywords" :key="t" :label="t" :value="t" />
                </el-select>
              </template>
            </td>
            <td style="padding:8px 12px">
              <el-tag v-if="entry.status === 'done'" type="success" size="small">完成</el-tag>
              <el-tag v-else-if="entry.status === 'error'" type="danger" size="small">失败</el-tag>
              <el-tag v-else-if="entry.status === 'analyzing'" type="warning" size="small">分析中</el-tag>
              <el-tag v-else type="info" size="small">待分析</el-tag>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ===== 步骤 2：AI 分析中（单张模式） ===== -->
  <div v-if="analyzingAny && currentStep === 'analyze' && uploadMode === 'single'" class="analysis-panel">
    <div class="panel-title"><el-icon><Cpu /></el-icon>AI 正在分析中...</div>
    <div style="display:flex;align-items:center;gap:12px;padding:12px 0">
      <el-progress :percentage="100" :indeterminate="true" :stroke-width="4" style="flex:1" />
      <span style="font-size:12px;color:#909399;white-space:nowrap">正在调用 Qwen3-VL 分析...</span>
    </div>
  </div>

  <!-- ===== 单张模式：当前活跃图片的分析结果 + 可编辑表单 ===== -->
  <div v-if="activeEntry?.analyzed && currentStep === 'upload' && uploadMode === 'single'">
    <!-- 图片切换提示 -->
    <div v-if="singleEntries.length > 1" style="margin-bottom:12px;font-size:13px;color:#606266">
      当前编辑：<b style="color:#7C3AED">{{ activeEntry.name }}</b>
      （点击上方缩略图切换到其他图片）
    </div>

    <!-- 分析结果展示 -->
    <div class="analysis-panel">
      <div class="panel-title">
        <el-icon><Cpu /></el-icon>AI 图片分析结果
        <el-tag size="small" type="success" style="margin-left:8px">{{ activeEntry.model }}</el-tag>
      </div>

      <!-- 可复现提示词 -->
      <div style="background:#f5f7fa;border-radius:6px;padding:10px 14px;margin-bottom:10px">
        <div style="font-size:11px;color:#909399;margin-bottom:4px">可复现提示词（Prompt）</div>
        <div style="font-size:13px;color:#303133;line-height:1.6">{{ activeEntry.prompt }}</div>
      </div>

      <!-- 摘要 -->
      <div style="background:#fff;border-radius:6px;padding:10px 14px;margin-bottom:10px">
        <div style="font-size:11px;color:#909399;margin-bottom:4px">摘要（Summary）</div>
        <div style="font-size:13px;color:#303133;line-height:1.6">{{ activeEntry.summary }}</div>
      </div>

      <!-- 关键词 -->
      <div style="background:#fff;border-radius:6px;padding:10px 14px">
        <div style="font-size:11px;color:#909399;margin-bottom:6px">关键词</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <el-tag v-for="kw in activeEntry.keywords" :key="kw" type="primary" size="small">{{ kw }}</el-tag>
        </div>
      </div>
    </div>

    <!-- 可编辑表单 -->
    <div class="upload-confirm-card" style="background:#fff;border-radius:8px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
      <h3 style="margin-bottom:16px;font-size:15px;display:flex;align-items:center;gap:8px">
        确认素材信息
        <span style="font-size:12px;color:#909399;font-weight:400">AI 已自动填写可复现提示词，可手动修改</span>
      </h3>
      <el-form label-width="80px">
        <el-form-item label="提示词">
          <el-input v-model="singleEntries[activeIndex].editedPrompt" type="textarea" :rows="3" placeholder="可复现提示词（用于语义检索）" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="singleEntries[activeIndex].editedKeywords" multiple placeholder="AI 建议的标签" style="width:100%" filterable allow-create>
            <el-option v-for="t in store.allTags" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="formSource" placeholder="设计部、外包团队..." />
        </el-form-item>
        <el-form-item>
          <div class="upload-action-row" style="display:flex;gap:8px">
            <el-button type="primary" size="large" :loading="uploading" @click="confirmAndUpload">
              <el-icon><UploadFilled /></el-icon> 确认上传（{{ singleEntries.length }} 个文件）
            </el-button>
            <el-button size="large" @click="runAnalysis">重新分析当前图片</el-button>
            <el-button size="large" @click="singleEntries=[];currentStep='select';clearDraft()">重新选择</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>

  <!-- ===== ZIP 模式：批量上传按钮 ===== -->
  <div v-if="hasZipEntries && currentStep === 'upload' && uploadMode === 'zip'" class="upload-confirm-card" style="background:#fff;border-radius:8px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-top:16px">
    <h3 style="margin-bottom:16px;font-size:15px">
      确认批量上传
      <span style="font-size:12px;color:#909399;font-weight:400">每张图片用各自的可复现提示词</span>
    </h3>
    <el-form label-width="80px">
      <el-form-item label="来源">
        <el-input v-model="formSource" placeholder="设计部、外包团队..." />
      </el-form-item>
      <el-form-item>
        <div class="upload-action-row" style="display:flex;gap:8px">
          <el-button type="primary" size="large" :loading="uploading" @click="confirmAndUpload">
            <el-icon><UploadFilled /></el-icon> 确认批量上传（{{ zipResults.filter(r => r.status === 'done').length }} / {{ zipResults.length }} 张）
          </el-button>
          <el-button size="large" @click="runZipAnalysis">重新分析</el-button>
          <el-button size="large" @click="switchToSingle">取消</el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
  </div>
</template>

<style scoped>
.upload-page {
  max-width: 1120px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .upload-steps {
    flex-direction: column !important;
    gap: 10px !important;
  }

  .upload-step-card {
    padding: 12px 14px !important;
    align-items: flex-start !important;
  }

  .upload-section-header {
    align-items: flex-start !important;
    flex-direction: column !important;
    gap: 10px !important;
  }

  .upload-action-row {
    width: 100%;
    flex-wrap: wrap !important;
    gap: 8px !important;

    :deep(.el-button) {
      flex: 1 1 140px;
      margin-left: 0 !important;
    }
  }

  .upload-thumb-list {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px !important;
  }

  .upload-thumb-item {
    width: auto !important;

    img {
      width: 100% !important;
      height: 96px !important;
    }
  }

  .upload-table-wrap {
    border-radius: var(--radius-md) !important;
  }

  .upload-confirm-card {
    padding: var(--space-4) !important;

    h3 {
      flex-direction: column;
      align-items: flex-start !important;
      gap: 4px !important;
      line-height: 1.4;
    }

    :deep(.el-form) {
      .el-form-item {
        display: block;
      }

      .el-form-item__label {
        justify-content: flex-start;
        margin-bottom: 6px;
      }

      .el-form-item__content {
        margin-left: 0 !important;
      }
    }
  }
}
</style>
