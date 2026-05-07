<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAssetStore } from '@/stores/assets'

const router = useRouter()
const store = useAssetStore()

const localQuery = ref('')
const searchActiveTags = ref<string[]>([])
const searchSuggestions = ['咖啡','猫','金毛犬','跑车','蓝色科技背景','汉堡','年会合影','登录页设计']

function doSearch() {
  if (!localQuery.value.trim()) return
  store.doSearch(localQuery.value)
}

const searchResultTags = computed(() => {
  const s = new Set<string>()
  store.searchResults.forEach(r => r.tags.forEach(t => s.add(t)))
  return [...s]
})

const searchResultsFiltered = computed(() => {
  if (searchActiveTags.value.length === 0) return store.searchResults
  return store.searchResults.filter(r => searchActiveTags.value.some(t => r.tags.includes(t)))
})

function toggleSearchTag(t: string) {
  const i = searchActiveTags.value.indexOf(t)
  i >= 0 ? searchActiveTags.value.splice(i, 1) : searchActiveTags.value.push(t)
}

function goDetail(id: number) {
  router.push(`/asset/${id}`)
}
</script>

<template>
  <div class="search-hero">
    <h2>以文搜图 · Chinese-CLIP 语义检索</h2>
    <p class="sub">输入自然语言描述，AI 在 512 维语义空间中匹配最相似的图片</p>
    <el-input
      v-model="localQuery" size="large"
      placeholder="例如：蓝色科技感背景图、年会大合影、咖啡、猫..."
      style="max-width:600px" clearable
      @keyup.enter="doSearch"
    >
      <template #append>
        <el-button type="primary" @click="doSearch" :loading="store.searching">搜索</el-button>
      </template>
    </el-input>
    <div class="suggest-tags">
      <span style="font-size:12px;color:#c0c4cc">试试语义搜索：</span>
      <el-tag v-for="s in searchSuggestions" :key="s" type="info" plain size="small" style="cursor:pointer" @click="localQuery=s;doSearch()">{{ s }}</el-tag>
    </div>
  </div>

  <el-collapse v-if="store.searchResults.length===0 && !store.searchQuery && !store.searching" style="max-width:700px;margin:0 auto 20px">
    <el-collapse-item title="CLIP 语义搜索是如何工作的？" name="1">
      <div style="font-size:13px;color:#606266;line-height:2">
        <p><b>1. 图像入库：</b>Chinese-CLIP 图像编码器将图片映射为 <b>512 维向量</b>，存入 FAISS。</p>
        <p><b>2. 搜索：</b>中文文本经文本编码器生成 <b>512 维向量</b>。</p>
        <p><b>3. 匹配：</b>FAISS 计算余弦相似度，返回 Top-K 结果。</p>
        <p><b>4. 优势：</b>不依赖精确匹配，"蓝色科技背景"能找到没有"蓝色"标签、但视觉是蓝色科技风的图。</p>
      </div>
    </el-collapse-item>
  </el-collapse>

  <template v-if="store.searchResults.length > 0">
    <div class="tag-filter" style="margin-top:16px">
      <span style="font-size:13px;color:#606266">
        检索到 {{ store.searchResults.length }} 条 &nbsp;|&nbsp; 余弦相似度排序 &nbsp;|&nbsp; 继续筛选：
      </span>
      <el-tag v-for="t in searchResultTags" :key="t"
        :type="searchActiveTags.includes(t)?'':'info'"
        :effect="searchActiveTags.includes(t)?'dark':'plain'"
        style="cursor:pointer;margin-left:6px" size="small"
        @click="toggleSearchTag(t)"
      >{{ t }}</el-tag>
    </div>

    <div v-for="(r, i) in searchResultsFiltered" :key="r.id" class="search-result-item" style="cursor:pointer" @click="goDetail(r.id)">
      <img :src="r.thumb" class="result-thumb">
      <div class="result-info">
        <div class="result-name">{{ i + 1 }}. {{ r.name }}</div>
        <div class="result-desc">{{ r.desc }}</div>
        <div class="match-reasons">
          <el-tag v-for="m in r.matchReasons" :key="m" size="small" type="success" effect="plain">{{ m }}</el-tag>
        </div>
      </div>
      <div class="score-badge">
        <el-progress type="dashboard" :percentage="r.score" :width="56" :stroke-width="6"
          :color="r.score>90?'#67C23A':r.score>80?'#409EFF':'#E6A23C'">
          <template #default><span style="font-size:13px;font-weight:600">{{ r.score }}%</span></template>
        </el-progress>
        <div style="font-size:11px;color:#c0c4cc">相似度</div>
      </div>
    </div>
  </template>
  <el-empty v-else-if="store.searchQuery && store.searchResults.length===0 && !store.searching" description="未找到匹配的素材，试试换一种描述" />
</template>
