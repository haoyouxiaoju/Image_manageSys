<script setup lang="ts">
// 纯展示页，无需逻辑
</script>

<template>
  <h2 style="font-size:20px;margin-bottom:8px">AI 视觉分析能力说明</h2>
  <p style="color:#909399;margin-bottom:24px">了解 AI 如何理解图片内容，以及它在素材库中能做什么、不能做什么</p>

  <div class="info-cards">
    <div class="info-card">
      <h4><el-icon color="#7C3AED"><Cpu /></el-icon> 视觉 AI 是什么？</h4>
      <p>本系统使用 <b>Qwen3-VL 多模态大模型</b>（通义千问视觉语言模型），通过阿里云 DashScope API 提供图片分析服务。</p>
      <p style="margin-top:8px">上传每张图片时，AI 会自动生成<b>可复现提示词</b>、<b>内容摘要</b>和<b>关键词标签</b>，用于后续语义检索。</p>
    </div>
    <div class="info-card">
      <h4><el-icon color="#409EFF"><Opportunity /></el-icon> AI 视觉分析能做什么？</h4>
      <ul>
        <li><b>生成可复现提示词</b>：用于 Midjourney/Stable Diffusion 等工具复现类似图片</li>
        <li><b>内容摘要</b>：用 20-40 字概括画面核心内容</li>
        <li><b>关键词提取</b>：6-15 个实体名词和风格标签</li>
        <li><b>语义搜索</b>：通过文本描述检索匹配的图片</li>
        <li>识别<b>物体、场景、风格、色调</b>等多维度视觉特征</li>
      </ul>
    </div>
    <div class="info-card">
      <h4><el-icon color="#E6A23C"><WarningFilled /></el-icon> 当前局限性</h4>
      <ul>
        <li><b>分析耗时</b>：每次调用 Qwen3-VL 约需 3-10 秒</li>
        <li><b>API 依赖</b>：需要有效的 DashScope API Key</li>
        <li><b>精度受限于提示词工程</b>：复杂或抽象概念可能描述不够精确</li>
        <li><b>文件大小限制</b>：单张图片不超过 20MB</li>
      </ul>
    </div>
  </div>

  <div class="info-cards">
    <div class="info-card">
      <h4><el-icon color="#67C23A"><Histogram /></el-icon> 搜索技术栈</h4>
      <ul>
        <li><b>向量嵌入</b>：text-embedding-v4 模型将提示词转为高维向量</li>
        <li><b>向量数据库</b>：Qdrant 存储和检索向量，余弦相似度匹配</li>
        <li><b>Agent 搜索</b>：LLM 理解自然语言意图，多角度检索并生成匹配理由</li>
        <li><b>关键词增强</b>：AI 分析结果作为标签辅助筛选</li>
      </ul>
    </div>
    <div class="info-card">
      <h4><el-icon color="#409EFF"><Connection /></el-icon> 在本系统中的使用</h4>
      <ul>
        <li><b>上传时</b>：可选择调用 AI 分析图片，生成提示词和关键词</li>
        <li><b>搜索时</b>：Agent 理解搜索意图，多轮向量检索匹配</li>
        <li><b>详情页</b>：查看 AI 生成的可复现提示词和关键词</li>
        <li><b>去重优化</b>：前端分析结果直接传后端，避免重复 AI 调用</li>
      </ul>
    </div>
    <div class="info-card">
      <h4><el-icon color="#7C3AED"><Star /></el-icon> 数据字段说明</h4>
      <p>每张素材的 AI 分析结果包含：</p>
      <ul style="margin-top:8px">
        <li><b>prompt</b>：可复现提示词（用于 AI 绘图工具）</li>
        <li><b>summary</b>：画面核心内容摘要</li>
        <li><b>keywords</b>：实体名词和风格标签列表</li>
        <li><b>matchReasons</b>：搜索时 AI 生成的匹配理由</li>
      </ul>
    </div>
  </div>
</template>
