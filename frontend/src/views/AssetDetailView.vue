<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAssetStore } from '@/stores/assets'
import { ElMessage, ElMessageBox } from 'element-plus'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useAssetStore()

const asset = ref(store.getAssetById(Number(route.params.id)))
const detailLoading = ref(false)
const showAddTag = ref(false)
const newTag = ref('')

// Q1.1: 编辑模式
const isEditing = ref(false)
const editForm = reactive({ name: '', desc: '', source: '' })

onMounted(async () => {
  detailLoading.value = true
  asset.value = await store.fetchAssetById(Number(route.params.id))
  detailLoading.value = false
  checkDeletePermission()
})

function enterEdit() {
  if (!asset.value) return
  editForm.name = asset.value.name
  editForm.desc = asset.value.desc
  editForm.source = asset.value.source
  isEditing.value = true
}

async function saveEdit() {
  if (!asset.value) return
  await store.updateAsset(asset.value.id, {
    name: editForm.name,
    desc: editForm.desc,
    source: editForm.source,
  })
  asset.value = store.getAssetById(asset.value.id)
  isEditing.value = false
  ElMessage.success('素材信息已更新')
}

function cancelEdit() {
  isEditing.value = false
}

function removeTag(t: string) {
  if (asset.value) store.removeAssetTag(asset.value.id, t)
}
function addTag(v: string) {
  if (v && asset.value) store.addAssetTag(asset.value.id, v)
  showAddTag.value = false
  newTag.value = ''
}
function copyShareLink() {
  const link = `https://clip-image.example.com/share/${asset.value?.id}/${Date.now()}`
  navigator.clipboard.writeText(link).then(() => ElMessage.success('分享链接已复制，有效期24小时'))
}

// Q4.1: 下载走后端 API
function downloadAsset() {
  if (!asset.value) return
  ElMessage.info(`模拟下载：GET /api/v1/assets/${asset.value.id}/download → 文件流 + 审计日志`)
  // 真实实现：
  // const resp = await fetch(`/api/v1/assets/${asset.value.id}/download`, { headers: { Authorization: `Bearer ${auth.token}` } })
  // const blob = await resp.blob()
  // const url = URL.createObjectURL(blob)
  // const a = document.createElement('a'); a.href = url; a.download = asset.value.name; a.click()
  // URL.revokeObjectURL(url)
}

// Q5.2: editor 只能删自己的，admin 可以删全部
const canDelete = ref(false)
function checkDeletePermission() {
  if (!asset.value || auth.isGuest) { canDelete.value = false; return }
  if (auth.isAdmin) { canDelete.value = true; return }
  if (auth.isEditor && asset.value.author === auth.user?.username) { canDelete.value = true; return }
  canDelete.value = false
}
onMounted(() => { checkDeletePermission() })

async function deleteAsset() {
  if (!asset.value) return
  try {
    await ElMessageBox.confirm('确定删除该素材吗？此操作不可撤销。', '确认删除', { type: 'warning' })
    await store.deleteAsset(asset.value!.id)
    ElMessage.success('素材已删除')
    router.push('/assets')
  } catch { /* 取消删除 */ }
}

// #1: 版本上传
const showVersionDialog = ref(false)
const versionForm = reactive({ file: null as File | null, tag: '', note: '' })
const versionFileInput = ref<HTMLInputElement | null>(null)

function openVersionDialog() {
  if (!asset.value) return
  // 自动建议下一版本号
  const latest = asset.value.versions[0]
  if (latest) {
    const parts = latest.version.replace('v', '').split('.')
    const minor = parseInt(parts[1] || '0') + 1
    versionForm.tag = `v${parts[0]}.${minor}`
  } else {
    versionForm.tag = 'v1.0'
  }
  versionForm.note = ''
  versionForm.file = null
  showVersionDialog.value = true
}

function onVersionFileSelected(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files && files.length > 0) versionForm.file = files[0]
}

function submitVersion() {
  if (!asset.value || !versionForm.file) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  const today = new Date().toISOString().split('T')[0]
  store.addVersion(asset.value.id, {
    version: versionForm.tag || `v${Date.now() % 100}`,
    note: versionForm.note || '新增版本',
    date: today,
  })
  // 更新 asset 引用
  asset.value = store.getAssetById(asset.value.id)
  ElMessage.success(`版本 ${versionForm.tag} 已上传`)
  showVersionDialog.value = false
}
</script>

<template>
  <LoadingSkeleton v-if="detailLoading" type="detail" />
  <div v-else-if="asset" style="max-width:720px">
    <el-button :icon="ArrowLeft" @click="router.back()" style="margin-bottom:16px">返回</el-button>

    <img :src="asset.thumb" class="drawer-image">

    <!-- 查看模式 -->
    <template v-if="!isEditing">
      <div class="meta-row"><span class="meta-label">名称</span><span class="meta-value">{{ asset.name }}</span></div>
      <div class="meta-row"><span class="meta-label">上传者</span><span class="meta-value">{{ asset.author }}</span></div>
      <div class="meta-row"><span class="meta-label">日期</span><span class="meta-value">{{ asset.date }}</span></div>
      <div class="meta-row"><span class="meta-label">描述</span><span class="meta-value">{{ asset.desc }}</span></div>
      <div class="meta-row"><span class="meta-label">来源</span><span class="meta-value">{{ asset.source }}</span></div>
      <div class="meta-row"><span class="meta-label">尺寸</span><span class="meta-value">{{ asset.size }}</span></div>
      <div class="meta-row"><span class="meta-label">格式</span><span class="meta-value">{{ asset.format }}</span></div>
      <div style="margin-bottom:12px">
        <el-button v-if="!auth.isGuest" size="small" :icon="Edit" @click="enterEdit">编辑信息</el-button>
      </div>
    </template>

    <!-- 编辑模式 -->
    <template v-else>
      <el-form label-width="60px" label-position="left">
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.desc" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="editForm.source" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" @click="saveEdit">保存</el-button>
          <el-button size="small" @click="cancelEdit">取消</el-button>
        </el-form-item>
      </el-form>
      <div class="meta-row"><span class="meta-label">尺寸</span><span class="meta-value">{{ asset.size }}</span></div>
      <div class="meta-row"><span class="meta-label">格式</span><span class="meta-value">{{ asset.format }}</span></div>
    </template>

    <div class="meta-row">
      <span class="meta-label">标签</span>
      <span style="display:flex;gap:6px;flex-wrap:wrap">
        <el-tag v-for="t in asset.tags" :key="t" closable size="small" @close="removeTag(t)">{{ t }}</el-tag>
        <el-button v-if="!auth.isGuest" size="small" :icon="Plus" circle @click="showAddTag=true" />
        <el-select v-if="showAddTag" v-model="newTag" size="small" placeholder="添加" style="width:100px" filterable allow-create @change="addTag" @blur="showAddTag=false" />
      </span>
    </div>

    <div v-if="asset.clipDesc" class="clip-panel" style="margin-top:16px">
      <div class="panel-title"><el-icon><Cpu /></el-icon>CLIP 语义理解</div>
      <div style="font-size:13px;color:#606266;line-height:1.8">
        <p><b>语义描述：</b>{{ asset.clipDesc }}</p>
        <p><b>视觉风格：</b>{{ asset.clipStyle }}</p>
        <p><b>色彩倾向：</b>{{ asset.clipColor }}</p>
        <p><b>向量：</b>512 维 · FAISS 索引 #{{ asset.id }}</p>
      </div>
    </div>

    <div style="display:flex;align-items:center;justify-content:space-between;margin:20px 0 10px">
      <h3 style="font-size:14px;color:#606266;margin:0">版本历史</h3>
      <el-button v-if="!auth.isGuest" size="small" :icon="Upload" @click="openVersionDialog">上传新版本</el-button>
    </div>
    <div v-for="(v, i) in asset.versions" :key="i" class="version-item">
      <div><span class="v-tag">{{ v.version }}</span><span style="margin-left:10px;font-size:13px;color:#606266">{{ v.note }}</span></div>
      <div style="font-size:12px;color:#c0c4cc">{{ v.date }}</div>
    </div>

    <div style="margin-top:24px;display:flex;gap:12px">
      <el-button type="primary" :icon="Download" @click="downloadAsset">下载原图</el-button>
      <el-button :icon="Share" @click="copyShareLink">复制分享链接</el-button>
      <el-button v-if="canDelete" type="danger" :icon="Delete" plain @click="deleteAsset">删除</el-button>
    </div>
  </div>

  <!-- #1: 版本上传对话框 -->
  <el-dialog v-model="showVersionDialog" title="上传新版本" width="440px">
    <el-form label-width="70px">
      <el-form-item label="选择文件">
        <input type="file" ref="versionFileInput" accept="image/jpeg,image/png,image/webp" @change="onVersionFileSelected" style="display:block">
        <span v-if="versionForm.file" style="font-size:12px;color:#67C23A;margin-top:4px;display:block">
          已选择：{{ versionForm.file.name }}
        </span>
      </el-form-item>
      <el-form-item label="版本号">
        <el-input v-model="versionForm.tag" placeholder="例如 v1.1" />
      </el-form-item>
      <el-form-item label="变更说明">
        <el-input v-model="versionForm.note" type="textarea" :rows="2" placeholder="说明此版本的变更内容" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showVersionDialog = false">取消</el-button>
      <el-button type="primary" @click="submitVersion">上传</el-button>
    </template>
  </el-dialog>

  <el-empty v-if="!detailLoading && !asset" description="素材未找到" />
</template>
