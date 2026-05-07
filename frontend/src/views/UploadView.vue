<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAssetStore } from '@/stores/assets'
import { ElMessage } from 'element-plus'
import type { UploadFormData, AssetVersion } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const store = useAssetStore()

const dragOver = ref(false)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const uploadFiles = ref<{ name:string; preview:string; status:string; progress:number; file:File }[]>([])
const uploadForm = ref<UploadFormData>({ desc: '', tags: [], source: '' })
const clipAnalysis = ref<{
  features: { label:string; value:string; conf:number; icon:string; bg:string; color:string }[]
  suggestedTags: string[]
  semanticDesc: string
} | null>(null)

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
    uploadFiles.value.push({
      name: f.name, preview: URL.createObjectURL(f),
      status: 'waiting', progress: 0, file: f,
    })
  })
  clipAnalysis.value = null
}
function toggleUploadTag(t: string) {
  const i = uploadForm.value.tags.indexOf(t)
  i >= 0 ? uploadForm.value.tags.splice(i, 1) : uploadForm.value.tags.push(t)
}

function hashStr(s: string): number {
  let h = 5381; for (let i = 0; i < s.length; i++) h = ((h << 5) + h) + s.charCodeAt(i)
  return Math.abs(h)
}

function simulateCLIPAnalysis() {
  const styleOptions = ['商业摄影棚拍','UI设计稿','平面设计/海报','风光摄影','建筑摄影','数字合成图','室内摄影','航拍摄影','插画风格']
  const colorOptions = ['蓝色/冷色调','暖黄/橙色','白色/中性色','红色/金色','深色/暗色调','绿色/自然色','粉色/柔和色','高饱和度彩色']
  const tagPool = ['科技','蓝色','背景','UI','App','海报','产品','人物','风景','建筑','设计','摄影','室内','室外','商务','简约','现代']
  const descTemplates = ['该图片呈现{style}特征，{color}为主视觉色调','{style}图片，整体色调为{color}']

  const nameHash = hashStr(uploadFiles.value[0]?.name || 'unknown')
  const style = styleOptions[nameHash % styleOptions.length]
  const color = colorOptions[(nameHash >> 4) % colorOptions.length]
  const ti = nameHash % tagPool.length
  const suggestedTags = [...new Set([tagPool[ti], tagPool[(ti+3)%tagPool.length], tagPool[(ti+7)%tagPool.length], uploadForm.value.tags[0]].filter(Boolean))]
  const desc = descTemplates[nameHash % descTemplates.length].replace('{style}', style).replace('{color}', color)

  clipAnalysis.value = {
    features: [
      { label:'视觉风格', value:style, conf:85+(nameHash%15), icon:'PictureFilled', bg:'#ecf5ff', color:'#409EFF' },
      { label:'主色调',   value:color, conf:80+((nameHash>>3)%20), icon:'MagicStick', bg:'#fef0f0', color:'#F56C6C' },
      { label:'内容密度', value:['简洁','适中','丰富'][(nameHash>>6)%3], conf:70+((nameHash>>5)%25), icon:'Grid', bg:'#f0f9eb', color:'#67C23A' },
      { label:'光线条件', value:['自然光','室内灯光','混合光','平光'][(nameHash>>8)%4], conf:60+((nameHash>>7)%30), icon:'Sunny', bg:'#fdf6ec', color:'#E6A23C' },
    ],
    suggestedTags,
    semanticDesc: desc,
  }
  suggestedTags.forEach(t => { if (!uploadForm.value.tags.includes(t)) uploadForm.value.tags.push(t) })
}

function startUpload() {
  uploading.value = true
  uploadFiles.value.forEach(f => { if (f.status !== 'done') f.status = 'analyzing' })

  setTimeout(() => {
    simulateCLIPAnalysis()
    uploadFiles.value.forEach(f => { if (f.status !== 'done') { f.status = 'uploading'; f.progress = 0 } })

    uploadFiles.value.forEach(f => {
      if (f.status === 'done') return
      const timer = setInterval(() => {
        f.progress += 15
        if (f.progress >= 100) {
          f.progress = 100; f.status = 'done'; clearInterval(timer)

          // ★ 写入共享 Store
          const today = new Date().toISOString().split('T')[0]
          const version: AssetVersion = { version: 'v1.0', note: 'CLIP 自动索引', date: today }
          store.addAsset({
            id: Date.now() + Math.floor(Math.random() * 1000),
            name: f.name.replace(/\.[^.]+$/, ''),
            desc: uploadForm.value.desc || clipAnalysis.value?.semanticDesc || f.name,
            thumb: f.preview,
            author: auth.user?.username || '当前用户',
            date: today,
            tags: uploadForm.value.tags.length > 0 ? [...uploadForm.value.tags] : ['未分类'],
            source: uploadForm.value.source || '未知来源',
            size: (f.file.size / 1024 / 1024).toFixed(1) + ' MB',
            format: f.name.split('.').pop()?.toUpperCase() || 'UNKNOWN',
            clipDesc: clipAnalysis.value?.semanticDesc || '',
            clipStyle: clipAnalysis.value?.features[0]?.value || '',
            clipColor: clipAnalysis.value?.features[1]?.value || '',
            clipTags: clipAnalysis.value?.suggestedTags || [],
            versions: [version],
          })
          ElMessage.success(`${f.name} 上传完成，CLIP 向量已索引`)
        }
      }, 250)
    })
    uploading.value = false
  }, 1500)
}
</script>

<template>
  <el-alert v-if="auth.isGuest" title="访客无法上传，请先登录编辑或管理员账号" type="warning" show-icon :closable="false" style="margin-bottom:20px" />

  <!-- 步骤 -->
  <div style="display:flex;gap:16px;margin-bottom:20px">
    <div v-for="(step, i) in ['选择图片','CLIP AI 分析','确认入库']" :key="i"
      style="flex:1;background:#fff;border-radius:8px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,0.06);display:flex;align-items:center;gap:12px"
      :style="{ opacity: (i === 0 || uploadFiles.length > 0) ? 1 : 0.6 }">
      <span style="width:28px;height:28px;border-radius:50%;background:#7C3AED;color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0">{{ i + 1 }}</span>
      <div><b style="font-size:14px;color:#303133">{{ step }}</b></div>
    </div>
  </div>

  <!-- 上传区 -->
  <div :class="['upload-zone', { dragover: dragOver }]"
    @click="triggerUpload" @dragover.prevent="dragOver=true" @dragleave="dragOver=false" @drop.prevent="onDrop">
    <div class="zone-icon"><el-icon><UploadFilled /></el-icon></div>
    <p style="font-size:16px;font-weight:600;color:#303133">点击或拖拽图片到此区域</p>
    <p class="sub">支持 JPG / PNG / WebP，单文件 ≤20MB · 上传后自动触发 CLIP AI 分析</p>
    <input type="file" ref="fileInput" multiple accept="image/jpeg,image/png,image/webp" style="display:none" @change="onFileSelect">
  </div>

  <!-- 预览 -->
  <div v-if="uploadFiles.length > 0" style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px">
    <div v-for="(f,i) in uploadFiles" :key="i" style="width:130px;text-align:center;background:#fff;border-radius:8px;padding:8px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
      <img :src="f.preview" style="width:114px;height:85px;object-fit:cover;border-radius:6px">
      <div style="font-size:12px;color:#606266;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ f.name }}</div>
      <el-tag :type="f.status==='done'?'success':f.status==='error'?'danger':f.status==='analyzing'?'':'warning'" size="small">
        {{ f.status==='done'?'完成':f.status==='error'?'失败':f.status==='analyzing'?'分析中...':'等待' }}
      </el-tag>
      <div v-if="f.status==='uploading'" style="margin-top:4px"><el-progress :percentage="f.progress" :stroke-width="4" /></div>
      <div v-if="f.status==='analyzing'" style="margin-top:4px"><el-progress :percentage="50" :stroke-width="4" :indeterminate="true" /></div>
    </div>
  </div>

  <!-- CLIP 分析结果 -->
  <div v-if="clipAnalysis" class="clip-panel">
    <div class="panel-title"><el-icon><Cpu /></el-icon>CLIP AI 分析结果</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px">
      <div v-for="f in clipAnalysis.features" :key="f.label" style="display:flex;align-items:center;gap:8px;background:#fff;border-radius:6px;padding:10px 14px">
        <div style="width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px" :style="{background:f.bg,color:f.color}">
          <el-icon><component :is="f.icon"/></el-icon>
        </div>
        <div>
          <div style="font-size:12px;color:#909399">{{ f.label }}</div>
          <div style="font-size:14px;font-weight:500;color:#303133">{{ f.value }}</div>
        </div>
        <div style="margin-left:auto"><el-progress type="circle" :percentage="f.conf" :width="40" :stroke-width="4" :color="f.color" /></div>
      </div>
    </div>
    <div style="margin-top:14px;padding-top:14px;border-top:1px solid #e0d4f5;font-size:13px;color:#606266">
      <b>CLIP 语义描述：</b>{{ clipAnalysis.semanticDesc }}
    </div>
  </div>

  <!-- 表单 -->
  <div v-if="uploadFiles.length > 0" style="background:#fff;border-radius:8px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
    <h3 style="margin-bottom:16px;font-size:15px">素材元数据</h3>
    <el-form label-width="80px">
      <el-form-item label="描述">
        <el-input v-model="uploadForm.desc" type="textarea" :rows="2" placeholder="补充描述..." />
      </el-form-item>
      <el-form-item label="标签">
        <el-select v-model="uploadForm.tags" multiple placeholder="选择标签" style="width:100%" filterable allow-create>
          <el-option v-for="t in store.allTags" :key="t" :label="t" :value="t" />
        </el-select>
      </el-form-item>
      <el-form-item label="来源">
        <el-input v-model="uploadForm.source" placeholder="设计部、外包团队..." />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="startUpload" :disabled="uploading" :loading="uploading">
          {{ uploading ? '处理中...' : '开始上传 + CLIP AI 分析' }}
        </el-button>
        <el-button @click="uploadFiles=[];clipAnalysis=null">清空</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
