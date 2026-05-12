<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAssetStore } from '@/stores/assets'

const router = useRouter()
const store = useAssetStore()

const localQuery = ref('')
const searchActiveTags = ref<string[]>([])
const searchSuggestions = ['咖啡','猫','金毛犬','跑车','蓝色科技背景','汉堡','年会合影','登录页设计']

// Q3.2: 搜索分页
const searchPage = ref(1)
const searchPageSize = 10

function doSearch() {
  if (!localQuery.value.trim()) return
  searchPage.value = 1
  store.doSearch(localQuery.value)
}

const searchResultTags = computed(() => {
  const s = new Set<string>()
  store.searchResults.forEach(r => r.tags.forEach(t => s.add(t)))
  return [...s]
})

const searchResultsFiltered = computed(() => {
  let arr = searchActiveTags.value.length === 0
    ? store.searchResults
    : store.searchResults.filter(r => searchActiveTags.value.some(t => r.tags.includes(t)))
  return arr
})

const pagedSearchResults = computed(() => {
  const start = (searchPage.value - 1) * searchPageSize
  return searchResultsFiltered.value.slice(start, start + searchPageSize)
})

function toggleSearchTag(t: string) {
  const i = searchActiveTags.value.indexOf(t)
  i >= 0 ? searchActiveTags.value.splice(i, 1) : searchActiveTags.value.push(t)
  searchPage.value = 1
}

function goDetail(id: number) {
  router.push(`/asset/${id}`)
}
</script>

<template>
  <div class="search-hero">
    <h2>以文搜图 · AI 语义检索</h2>
    <p class="sub">输入自然语言描述，AI 在语义空间中匹配最相似的图片</p>
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
    <el-collapse-item title="AI 语义搜索是如何工作的？" name="1">
      <div style="font-size:13px;color:#606266;line-height:2">
        <p><b>1. 图像入库：</b>Qwen3-VL 模型分析图片内容，生成可复现提示词，存入 Qdrant 向量数据库。</p>
        <p><b>2. 搜索：</b>Agent 理解用户意图，调用向量搜索引擎从多角度检索匹配的图片。</p>
        <p><b>3. 匹配：</b>LLM 多轮检索 + 语义匹配，为每张图片生成中文匹配理由。</p>
        <p><b>4. 优势：</b>不依赖精确匹配，"蓝色科技背景"能找到没有"蓝色"标签、但视觉是蓝色科技风的图。</p>
      </div>
    </el-collapse-item>
  </el-collapse>

  <template v-if="store.searchResults.length > 0">
    <div v-if="store.searchReasoning" class="reasoning-box" style="margin-top:16px;background:#f0f9ff;border:1px solid #b3d8ff;border-radius:8px;padding:12px 16px">
      <span style="font-size:12px;color:#409eff;font-weight:600">AI 推理过程：</span>
      <span style="font-size:13px;color:#303133">{{ store.searchReasoning }}</span>
    </div>
    <div class="tag-filter" style="margin-top:16px">
      <span style="font-size:13px;color:#606266">
        检索到 {{ store.searchResults.length }} 条 &nbsp;|&nbsp; Agent 语义匹配排序 &nbsp;|&nbsp; 继续筛选：
      </span>
      <el-tag v-for="t in searchResultTags" :key="t"
        :type="searchActiveTags.includes(t)?'':'info'"
        :effect="searchActiveTags.includes(t)?'dark':'plain'"
        style="cursor:pointer;margin-left:6px" size="small"
        @click="toggleSearchTag(t)"
      >{{ t }}</el-tag>
    </div>

    <div v-for="(r, i) in pagedSearchResults" :key="r.id" class="search-result-item" style="cursor:pointer" @click="goDetail(r.id)">
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
  <!-- 搜索分页 -->
  <div class="pagination-wrap" v-if="searchResultsFiltered.length > searchPageSize">
    <el-pagination
      background
      layout="prev, pager, next, total"
      :total="searchResultsFiltered.length"
      :page-size="searchPageSize"
      v-model:current-page="searchPage"
    />
  </div>

  <el-empty v-else-if="store.searchQuery && store.searchResults.length===0 && !store.searching" description="未找到匹配的素材，试试换一种描述" />
</template>
