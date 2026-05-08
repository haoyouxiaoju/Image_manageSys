<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAssetStore } from '@/stores/assets'
import { ElMessage } from 'element-plus'
import { clipApi } from '@/api/clip'

const auth = useAuthStore()
const store = useAssetStore()

// ---- 步骤控制 ----
type Step = 'select' | 'analyze' | 'upload'
const currentStep = ref<Step>('select')

// ---- 文件 ----
const dragOver = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const uploadFiles = ref<{ name: string; preview: string; file: File }[]>([])

// ---- 表单（CLIP 分析后自动填充） ----
const formDesc = ref('')
const formTags = ref<string[]>([])
const formSource = ref('')

// ---- CLIP 分析 ----
const analyzing = ref(false)
const clipResult = ref<{
  model: string
  features: { style?: string; color_tone?: string; scene?: string; objects?: string[] }
  suggested_description: string
  suggested_tags: string[]
} | null>(null)

// ---- 上传 ----
const uploading = ref(false)
const uploadProgress = ref<Record<string, number>>({})

// ===== 文件操作 =====
function triggerUpload() {
  if (!auth.isGuest) fileInput.value?.click()
}
function onFileSelect(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files) addFiles(Array.from(files))
}
function onDrop(e: DragEvent) {
  dragOver.value = false
  const files = e.dataTransfer?.files
  if (files) addFiles(Array.from(files).filter(f => f.type.startsWith('image/')))
}
function addFiles(files: File[]) {
  files.forEach(f => {
    if (!uploadFiles.value.find(x => x.name === f.name)) {
      uploadFiles.value.push({ name: f.name, preview: URL.createObjectURL(f), file: f })
    }
  })
  currentStep.value = 'select'
  clipResult.value = null
}

function removeFile(idx: number) {
  uploadFiles.value.splice(idx, 1)
}

const hasFiles = computed(() => uploadFiles.value.length > 0)

// ===== 步骤 2：CLIP AI 分析 =====
async function runCLIPAnalysis() {
  if (!hasFiles.value) return
  analyzing.value = true
  currentStep.value = 'analyze'

  try {
    const fd = new FormData()
    fd.append('file', uploadFiles.value[0].file)

    const res = await clipApi.analyze(fd)
    const data = res.data

    clipResult.value = {
      model: data.model,
      features: data.features,
      suggested_description: data.suggested_description,
      suggested_tags: data.suggested_tags,
    }

    // 自动填充表单
    formDesc.value = data.suggested_description
    formTags.value = [...data.suggested_tags]
    formSource.value = formSource.value || ''

    currentStep.value = 'upload'
  } catch (e: any) {
    ElMessage.error('CLIP 分析失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
    currentStep.value = 'select'
  } finally {
    analyzing.value = false
  }
}

// ===== 步骤 3：确认并上传 =====
async function confirmAndUpload() {
  uploading.value = true
  let successCount = 0
  let failCount = 0

  for (const f of uploadFiles.value) {
    uploadProgress.value[f.name] = 0
    try {
      const fd = new FormData()
      fd.append('file', f.file)
      fd.append('name', f.name.replace(/\.[^.]+$/, ''))
      fd.append('description', formDesc.value)
      fd.append('source', formSource.value)

      await store.uploadAsset(fd, (e: ProgressEvent) => {
        if (e.total) uploadProgress.value[f.name] = Math.round((e.loaded / e.total) * 100)
      })
      uploadProgress.value[f.name] = 100
      successCount++
    } catch (e: any) {
      uploadProgress.value[f.name] = -1
      failCount++
      ElMessage.error(`${f.name} 上传失败：${e?.response?.data?.error?.message || e?.message || '未知错误'}`)
    }
  }

  uploading.value = false

  if (failCount === 0) {
    ElMessage.success(`全部 ${successCount} 个文件上传完成`)
    // 重置
    uploadFiles.value = []
    formDesc.value = ''
    formTags.value = []
    formSource.value = ''
    clipResult.value = null
    currentStep.value = 'select'
  } else if (successCount > 0) {
    ElMessage.warning(`${successCount} 个成功，${failCount} 个失败`)
  }
}

// ===== 步骤状态 =====
const stepStatus = computed(() => ({
  select: currentStep.value === 'select' ? 'active' : currentStep.value === 'analyze' || currentStep.value === 'upload' ? 'done' : 'pending',
  analyze: currentStep.value === 'analyze' ? 'active' : currentStep.value === 'upload' ? 'done' : 'pending',
  upload: currentStep.value === 'upload' ? 'active' : 'pending',
}))
</script>

<template>
  <el-alert v-if="auth.isGuest" title="访客无法上传，请先登录编辑或管理员账号" type="warning" show-icon :closable="false" style="margin-bottom:20px" />

  <!-- ===== 步骤指示器 ===== -->
  <div style="display:flex;gap:16px;margin-bottom:20px">
    <div v-for="(step, i) in [
      { key:'select', label:'选择图片', desc:'点击或拖拽选择文件' },
      { key:'analyze', label:'CLIP AI 分析', desc:'自动识别内容并填写信息' },
      { key:'upload', label:'确认上传', desc:'检查信息后提交入库' },
    ]" :key="step.key"
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
  <div :class="['upload-zone', { dragover: dragOver }]"
    @click="triggerUpload" @dragover.prevent="dragOver=true" @dragleave="dragOver=false" @drop.prevent="onDrop">
    <div class="zone-icon"><el-icon><UploadFilled /></el-icon></div>
    <p style="font-size:16px;font-weight:600;color:#303133">点击或拖拽图片到此区域</p>
    <p class="sub">支持 JPG / PNG / WebP，单文件 ≤20MB</p>
    <input type="file" ref="fileInput" multiple accept="image/jpeg,image/png,image/webp" style="display:none" @change="onFileSelect">
  </div>

  <!-- 文件列表 -->
  <div v-if="hasFiles" style="margin-bottom:20px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <span style="font-size:14px;color:#606266">已选择 <b>{{ uploadFiles.length }}</b> 个文件</span>
      <div style="display:flex;gap:8px">
        <el-button
          v-if="currentStep === 'select'"
          type="primary" :icon="Cpu"
          @click="runCLIPAnalysis"
        >CLIP AI 分析</el-button>
      </div>
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      <div v-for="(f, i) in uploadFiles" :key="i"
        style="position:relative;width:130px;text-align:center;background:#fff;border-radius:8px;padding:8px;box-shadow:0 1px 4px rgba(0,0,0,0.06)"
      >
        <img :src="f.preview" style="width:114px;height:85px;object-fit:cover;border-radius:6px">
        <div style="font-size:12px;color:#606266;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ f.name }}</div>
        <div v-if="uploadProgress[f.name] !== undefined && uploadProgress[f.name] >= 0" style="margin-top:4px">
          <el-progress :percentage="uploadProgress[f.name]" :stroke-width="4" :status="uploadProgress[f.name] === 100 ? 'success' : undefined" />
        </div>
        <div v-else-if="uploadProgress[f.name] === -1" style="margin-top:4px">
          <el-tag type="danger" size="small">失败</el-tag>
        </div>
        <el-button v-if="currentStep === 'select'"
          style="position:absolute;top:2px;right:2px"
          size="small" type="danger" circle :icon="Close"
          @click="removeFile(i)"
        />
      </div>
    </div>
  </div>

  <!-- ===== 步骤 2：CLIP 分析中 ===== -->
  <div v-if="analyzing" class="clip-panel">
    <div class="panel-title"><el-icon><Cpu /></el-icon>CLIP 正在分析中...</div>
    <div style="display:flex;align-items:center;gap:12px;padding:12px 0">
      <el-progress :percentage="100" :indeterminate="true" :stroke-width="4" style="flex:1" />
      <span style="font-size:12px;color:#909399;white-space:nowrap">正在调用 Chinese-CLIP 编码...</span>
    </div>
  </div>

  <!-- ===== 步骤 2 完成：CLIP 分析结果 + 可编辑表单 ===== -->
  <div v-if="clipResult && currentStep === 'upload'">
    <!-- CLIP 结果展示 -->
    <div class="clip-panel">
      <div class="panel-title">
        <el-icon><Cpu /></el-icon>CLIP AI 分析结果
        <el-tag size="small" type="success" style="margin-left:8px">{{ clipResult.model }}</el-tag>
      </div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:12px">
        <div style="background:#fff;border-radius:6px;padding:10px 14px;text-align:center">
          <div style="font-size:11px;color:#909399">视觉风格</div>
          <div style="font-size:14px;font-weight:600;color:#303133;margin-top:2px">{{ clipResult.features.style || '-' }}</div>
        </div>
        <div style="background:#fff;border-radius:6px;padding:10px 14px;text-align:center">
          <div style="font-size:11px;color:#909399">色调</div>
          <div style="font-size:14px;font-weight:600;color:#303133;margin-top:2px">{{ clipResult.features.color_tone || '-' }}</div>
        </div>
        <div style="background:#fff;border-radius:6px;padding:10px 14px;text-align:center">
          <div style="font-size:11px;color:#909399">场景</div>
          <div style="font-size:14px;font-weight:600;color:#303133;margin-top:2px">{{ clipResult.features.scene || '-' }}</div>
        </div>
        <div style="background:#fff;border-radius:6px;padding:10px 14px;text-align:center">
          <div style="font-size:11px;color:#909399">物体</div>
          <div style="font-size:14px;font-weight:600;color:#303133;margin-top:2px">{{ (clipResult.features.objects || []).join('、') || '-' }}</div>
        </div>
      </div>
    </div>

    <!-- 可编辑表单 -->
    <div style="background:#fff;border-radius:8px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
      <h3 style="margin-bottom:16px;font-size:15px;display:flex;align-items:center;gap:8px">
        确认素材信息
        <span style="font-size:12px;color:#909399;font-weight:400">CLIP 已自动填写，可手动修改</span>
      </h3>
      <el-form label-width="80px">
        <el-form-item label="描述">
          <el-input v-model="formDesc" type="textarea" :rows="2" placeholder="CLIP 自动生成的描述" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="formTags" multiple placeholder="CLIP 建议的标签" style="width:100%" filterable allow-create>
            <el-option v-for="t in store.allTags" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="formSource" placeholder="设计部、外包团队..." />
        </el-form-item>
        <el-form-item>
          <div style="display:flex;gap:8px">
            <el-button type="primary" size="large" :loading="uploading" @click="confirmAndUpload">
              <el-icon><UploadFilled /></el-icon> 确认上传（{{ uploadFiles.length }} 个文件）
            </el-button>
            <el-button size="large" @click="runCLIPAnalysis">重新分析</el-button>
            <el-button size="large" @click="uploadFiles=[];clipResult=null;currentStep='select'">重新选择</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>
