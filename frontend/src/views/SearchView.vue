<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAssetStore } from '@/stores/assets'

const router = useRouter()
const store = useAssetStore()

const localQuery = ref('')
const searchActiveTags = ref<string[]>([])
const searchSuggestions = ['咖啡', '猫', '金毛犬', '跑车', '蓝色科技背景', '汉堡', '年会合影', '登录页设计']
const searchPage = ref(1)
const searchPageSize = 10

function doSearch() {
  if (!localQuery.value.trim()) return
  searchPage.value = 1
  store.doSearch(localQuery.value)
}

function applySuggestion(s: string) {
  localQuery.value = s
  doSearch()
}

const searchResultTags = computed(() => {
  const s = new Set<string>()
  store.searchResults.forEach(r => r.tags.forEach(t => s.add(t)))
  return [...s]
})

const searchResultsFiltered = computed(() => {
  if (searchActiveTags.value.length === 0) return store.searchResults
  return store.searchResults.filter(r =>
    searchActiveTags.value.some(t => r.tags.includes(t))
  )
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

const showExplain = ref(false)
</script>

<template>
  <div class="search-page">
    <!-- Hero -->
    <div class="search-hero animate-in">
      <h2>以文搜图</h2>
      <p class="search-subtitle">输入自然语言描述，AI 在语义空间中匹配最相似的图片</p>

      <!-- Search Bar -->
      <div class="search-bar-large">
        <span class="search-icon">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="8" cy="8" r="5.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M12.5 12.5L16 16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </span>
        <input
          v-model="localQuery"
          placeholder="例如：蓝色科技感背景图、年会大合影、咖啡..."
          @keyup.enter="doSearch"
          style="flex:1; border:none; background:transparent; font-size:16px; color:var(--text-primary); padding: 12px 0;"
        />
        <button class="search-btn" @click="doSearch" :disabled="store.searching">
          <span v-if="store.searching">搜索中…</span>
          <span v-else>搜索</span>
        </button>
      </div>

      <!-- Suggestions -->
      <div class="suggest-tags">
        <span style="font-size:12px; color: var(--text-tertiary)">试试：</span>
        <span
          v-for="s in searchSuggestions"
          :key="s"
          class="tag-chip"
          @click="applySuggestion(s)"
        >{{ s }}</span>
      </div>
    </div>

    <!-- AI Explain Toggle -->
    <div v-if="store.searchResults.length === 0 && !store.searchQuery" class="explain-toggle animate-in">
      <button class="explain-btn" @click="showExplain = !showExplain">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.3"/>
          <path d="M7 5V7.5M7 9V9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        AI 语义搜索是如何工作的？
        <svg
          width="12" height="12" viewBox="0 0 12 12" fill="none"
          :style="{ transform: showExplain ? 'rotate(180deg)' : '', transition: 'transform 200ms' }"
        >
          <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
      </button>
      <div v-if="showExplain" class="explain-content">
        <div class="explain-step">
          <span class="step-num">1</span>
          <div>
            <strong>图像入库</strong>
            <p>Qwen3-VL 模型分析图片内容，生成可复现描述，存入 Qdrant 向量数据库</p>
          </div>
        </div>
        <div class="explain-step">
          <span class="step-num">2</span>
          <div>
            <strong>语义搜索</strong>
            <p>Agent 理解用户意图，调用向量搜索引擎从多角度检索匹配的图片</p>
          </div>
        </div>
        <div class="explain-step">
          <span class="step-num">3</span>
          <div>
            <strong>LLM 重排序</strong>
            <p>多轮语义匹配，为每张图片生成中文匹配理由，返回相关度得分</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Reasoning Box -->
    <div v-if="store.searchReasoning" class="reasoning-box animate-in">
      <div class="reasoning-label">
        <span class="ai-dot"></span>
        AI 推理过程
      </div>
      <p class="reasoning-text">{{ store.searchReasoning }}</p>
    </div>

    <!-- Tag Filter -->
    <div class="tag-filter animate-in" v-if="store.searchResults.length > 0">
      <div class="tag-filter-title">
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
          <path d="M2 4.5C2 3.67 2.67 3 3.5 3H6L7.5 5H12.5C13.33 5 14 5.67 14 6.5V11.5C14 12.33 13.33 13 12.5 13H3.5C2.67 13 2 12.33 2 11.5V4.5Z" stroke="currentColor" stroke-width="1.3"/>
        </svg>
        标签筛选
      </div>
      <div class="tag-list">
        <span
          v-for="t in searchResultTags"
          :key="t"
          class="tag-chip"
          :class="{ active: searchActiveTags.includes(t) }"
          @click="toggleSearchTag(t)"
        >{{ t }}</span>
      </div>
    </div>

    <!-- Results -->
    <div v-if="store.searchResults.length > 0">
      <div class="results-meta animate-in">
        检索到 <strong>{{ store.searchResults.length }}</strong> 条结果 · Agent 语义匹配排序
      </div>

      <div class="search-results-list">
        <div
          v-for="r in pagedSearchResults"
          :key="r.id"
          class="search-result-item animate-in"
          @click="goDetail(r.id)"
        >
          <img :src="r.thumb" :alt="r.name" class="result-thumb" loading="lazy" />
          <div class="result-info">
            <div class="result-name">{{ r.name }}</div>
            <div class="result-desc">{{ r.desc }}</div>
            <div class="match-tags">
              <span v-for="m in r.matchReasons" :key="m" class="match-tag">{{ m }}</span>
            </div>
          </div>
          <div class="score-badge">
            <div class="score-ring">
              <svg viewBox="0 0 44 44" width="56" height="56">
                <circle cx="22" cy="22" r="18" fill="none" stroke="rgba(0,0,0,0.08)" stroke-width="4"/>
                <circle
                  cx="22" cy="22" r="18" fill="none"
                  :stroke="r.score > 90 ? '#34C759' : r.score > 80 ? '#007AFF' : '#FF9500'"
                  stroke-width="4"
                  stroke-linecap="round"
                  :stroke-dasharray="`${(r.score / 100) * 113} 113`"
                  transform="rotate(-90 22 22)"
                />
              </svg>
              <span class="score-num">{{ r.score }}<span style="font-size:11px">%</span></span>
            </div>
            <div class="score-label">相似度</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="store.searchQuery && store.searchResults.length === 0 && !store.searching" class="empty-state animate-in">
      <svg class="empty-icon" width="40" height="40" viewBox="0 0 40 40" fill="none">
        <circle cx="18" cy="18" r="11" stroke="currentColor" stroke-width="1.5"/>
        <path d="M26 26L33 33" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M14 18H22M18 14V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <div class="empty-title">未找到匹配的素材</div>
      <div class="empty-desc">试试换一种描述方式，或调整筛选标签</div>
    </div>

    <!-- Pagination -->
    <div class="pagination-wrap" v-if="searchResultsFiltered.length > searchPageSize">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="searchResultsFiltered.length"
        :page-size="searchPageSize"
        v-model:current-page="searchPage"
      />
    </div>
  </div>
</template>

<style scoped>
.search-page {
  max-width: 900px;
  margin: 0 auto;
}

.explain-toggle {
  max-width: 600px;
  margin: 0 auto var(--space-6);
}

.explain-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  padding: 8px 0;
  width: 100%;
  text-align: left;

  &:hover { color: var(--accent); }
}

.explain-content {
  background: var(--bg-surface);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--space-5) var(--space-6);
  margin-top: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.explain-step {
  display: flex;
  gap: var(--space-4);
  align-items: flex-start;

  .step-num {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--accent);
    color: white;
    font-size: 11px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  strong { font-size: 13px; font-weight: 600; color: var(--text-primary); display: block; margin-bottom: 2px; }
  p { font-size: 12px; color: var(--text-secondary); line-height: 1.6; margin: 0; }
}

.reasoning-box {
  background: var(--bg-surface);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--space-5) var(--space-6);
  margin-bottom: var(--space-5);
  display: flex;
  gap: var(--space-4);
  align-items: flex-start;

  .reasoning-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--accent);
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .reasoning-text {
    font-size: 13px;
    color: var(--text-primary);
    line-height: 1.7;
    margin: 0;
  }
}

.ai-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-purple);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.results-meta {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
  text-align: center;

  strong { color: var(--text-primary); font-weight: 600; }
}

.match-tag {
  display: inline-block;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(52, 199, 89, 0.1);
  color: var(--success);
  font-weight: 400;
}

.score-ring {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.score-num {
  position: absolute;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.score-label {
  font-size: 10px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: center;
  margin-top: 4px;
}

.search-results-list {
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .explain-toggle {
    max-width: none;
    margin-bottom: var(--space-4);
  }

  .explain-content {
    padding: var(--space-4);
  }

  .explain-step {
    gap: var(--space-3);
  }

  .reasoning-box {
    padding: var(--space-4);
  }
}
</style>
