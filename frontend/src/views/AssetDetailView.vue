<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAssetStore } from '@/stores/assets'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useAssetStore()

const asset = ref(store.getAssetById(Number(route.params.id)))
const showAddTag = ref(false)
const newTag = ref('')

// Q1.1: 编辑模式
const isEditing = ref(false)
const editForm = reactive({ name: '', desc: '', source: '' })

onMounted(() => {
  asset.value = store.getAssetById(Number(route.params.id))
})

function enterEdit() {
  if (!asset.value) return
  editForm.name = asset.value.name
  editForm.desc = asset.value.desc
  editForm.source = asset.value.source
  isEditing.value = true
}

function saveEdit() {
  if (!asset.value) return
  store.updateAsset(asset.value.id, {
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

function deleteAsset() {
  if (!asset.value) return
  ElMessageBox.confirm('确定删除该素材吗？此操作不可撤销。', '确认删除', { type: 'warning' }).then(() => {
    store.deleteAsset(asset.value!.id)
    ElMessage.success('素材已删除')
    router.push('/assets')
  }).catch(() => {})
}
</script>

<template>
  <div v-if="asset" style="max-width:720px">
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

    <h3 style="font-size:14px;margin:20px 0 10px;color:#606266">版本历史</h3>
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
  <el-empty v-else description="素材未找到" />
</template>
