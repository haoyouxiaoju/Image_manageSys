<script setup lang="ts">
// Pure display page, no logic needed
</script>

<template>
  <div class="vision-page">
    <!-- Header -->
    <div class="vision-header animate-in">
      <div class="vision-icon">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="14" fill="url(#grad)" opacity="0.15"/>
          <path d="M16 8L18.5 13.5L24 14.5L18.5 15.5L16 21L13.5 15.5L8 14.5L13.5 13.5L16 8Z" stroke="#AF52DE" stroke-width="1.5" stroke-linejoin="round"/>
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="32" y2="32">
              <stop offset="0%" stop-color="#AF52DE"/>
              <stop offset="100%" stop-color="#007AFF"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div>
        <h1>AI 视觉能力说明</h1>
        <p>了解 AI 如何理解图片内容，以及它在素材库中能做什么、不能做什么</p>
      </div>
    </div>

    <!-- Core Cards: How it works -->
    <div class="section-label animate-in">核心技术</div>
    <div class="info-cards">
      <div class="info-card animate-in">
        <h4>
          <svg class="icon-purple" width="18" height="18" viewBox="0 0 20 20" fill="none">
            <rect x="3" y="3" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
            <rect x="11" y="3" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
            <rect x="3" y="11" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
            <rect x="11" y="11" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          Qwen3-VL 多模态大模型
        </h4>
        <p>本系统使用阿里云 <b>Qwen3-VL</b>（通义千问视觉语言模型），上传每张图片时自动生成可复现提示词、内容摘要和关键词标签，用于语义检索。</p>
      </div>

      <div class="info-card animate-in">
        <h4>
          <svg class="icon-blue" width="18" height="18" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.3"/>
            <path d="M10 6V10.5L13 13" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          向量嵌入 + Qdrant 检索
        </h4>
        <p><b>text-embedding-v4</b> 将文本转为高维向量，<b>Qdrant</b> 向量数据库以余弦相似度匹配，最相关的图片排在最前面。</p>
      </div>

      <div class="info-card animate-in">
        <h4>
          <svg class="icon-purple" width="18" height="18" viewBox="0 0 20 20" fill="none">
            <path d="M10 3L12 8L17 8.5L13 12L14 17L10 14.5L6 17L7 12L3 8.5L8 8L10 3Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
          </svg>
          Agent 智能搜索
        </h4>
        <p>qwen-plus 函数调用理解自然语言意图，多角度检索并生成中文匹配理由，让搜索结果可解释、可追溯。</p>
      </div>
    </div>

    <!-- Capabilities -->
    <div class="section-label animate-in">AI 分析能力</div>
    <div class="info-cards">
      <div class="info-card animate-in">
        <h4>
          <svg class="icon-green" width="18" height="18" viewBox="0 0 20 20" fill="none">
            <path d="M10 3V7M10 13V17M3 10H7M13 10H17" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            <circle cx="10" cy="10" r="3" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          能做什么
        </h4>
        <ul>
          <li><b>可复现提示词</b>：可用于 Midjourney / Stable Diffusion 复现类似图片</li>
          <li><b>内容摘要</b>：20-40 字概括画面核心内容</li>
          <li><b>关键词提取</b>：6-15 个实体名词和风格标签</li>
          <li><b>多维度识别</b>：物体、场景、风格、色调等视觉特征</li>
        </ul>
      </div>

      <div class="info-card animate-in">
        <h4>
          <svg class="icon-orange" width="18" height="18" viewBox="0 0 20 20" fill="none">
            <path d="M10 3L12 8H17L13 11L14.5 16.5L10 13L5.5 16.5L7 11L3 8H8L10 3Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
            <path d="M7 7L8.5 8.5M11.5 8.5L13 7" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          当前局限性
        </h4>
        <ul>
          <li><b>分析耗时</b>：每次调用约需 3-10 秒</li>
          <li><b>API 依赖</b>：需要有效的 DashScope API Key</li>
          <li><b>精度限制</b>：复杂或抽象概念可能描述不够精确</li>
          <li><b>文件大小</b>：单张图片不超过 20MB</li>
        </ul>
      </div>

      <div class="info-card animate-in">
        <h4>
          <svg class="icon-blue" width="18" height="18" viewBox="0 0 20 20" fill="none">
            <rect x="3" y="6" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.3"/>
            <path d="M7 6V4.5C7 3.67 7.67 3 8.5 3H11.5C12.33 3 13 3.67 13 4.5V6" stroke="currentColor" stroke-width="1.3"/>
            <circle cx="10" cy="11" r="2" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          在本系统的使用
        </h4>
        <ul>
          <li><b>上传时</b>：可选调用 AI 分析，生成提示词和关键词</li>
          <li><b>搜索时</b>：Agent 理解意图，多轮向量检索匹配</li>
          <li><b>详情页</b>：查看 AI 生成的可复现提示词</li>
          <li><b>去重优化</b>：前端分析结果直传后端，避免重复调用</li>
        </ul>
      </div>
    </div>

    <!-- Data Fields -->
    <div class="section-label animate-in">数据字段说明</div>
    <div class="info-cards">
      <div class="info-card animate-in">
        <h4>
          <svg class="icon-purple" width="18" height="18" viewBox="0 0 20 20" fill="none">
            <path d="M10 3V7M10 13V17M3 10H7M13 10H17" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            <circle cx="10" cy="10" r="3" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          prompt · summary · keywords
        </h4>
        <ul>
          <li><b>prompt</b>：可复现提示词（AI 绘图工具用）</li>
          <li><b>summary</b>：画面核心内容摘要</li>
          <li><b>keywords</b>：实体名词和风格标签列表</li>
          <li><b>matchReasons</b>：搜索时 AI 生成的匹配理由</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vision-page {
  max-width: 1200px;
  margin: 0 auto;
}

.vision-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  margin-bottom: var(--space-8);
  padding: var(--space-6) var(--space-6);
  @include glass-card;

  h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    margin-bottom: var(--space-2);
  }

  p {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0;
  }
}

.vision-icon {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(175, 82, 222, 0.1), rgba(0, 122, 255, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
  margin-bottom: var(--space-3);
  margin-top: var(--space-5);
  padding-left: 4px;
}
</style>