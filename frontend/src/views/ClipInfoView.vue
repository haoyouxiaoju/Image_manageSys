<script setup lang="ts">
// 纯展示页，无需逻辑
</script>

<template>
  <h2 style="font-size:20px;margin-bottom:8px">Chinese-CLIP 能力说明</h2>
  <p style="color:#909399;margin-bottom:24px">了解 CLIP 如何理解图片，以及它在素材库中能做什么、不能做什么</p>

  <div class="info-cards">
    <div class="info-card">
      <h4><el-icon color="#7C3AED"><Cpu /></el-icon> CLIP 是什么？</h4>
      <p>CLIP（Contrastive Language-Image Pre-training）是<b>图文对比学习模型</b>。Chinese-CLIP 是其汉化版本，使用中文文本-图像对训练。</p>
      <p style="margin-top:8px">它将图片和文本映射到<b>同一个 512 维语义空间</b>，通过向量距离衡量匹配程度。</p>
    </div>
    <div class="info-card">
      <h4><el-icon color="#409EFF"><Opportunity /></el-icon> CLIP 能做什么？</h4>
      <ul>
        <li><b>识别具体物体</b>：猫、狗、咖啡、汉堡、汽车...（强项）</li>
        <li>理解<b>整体风格</b>（科技感、温暖、专业）</li>
        <li>识别<b>场景类型</b>（室内/户外、办公室、草地）</li>
        <li>捕捉<b>色彩倾向</b>（蓝色调、暖色调）</li>
        <li>图文跨模态检索：用文字搜图、用图搜图</li>
      </ul>
    </div>
    <div class="info-card">
      <h4><el-icon color="#E6A23C"><WarningFilled /></el-icon> CLIP 不擅长什么？</h4>
      <ul>
        <li><b>精确文字识别</b>：图片中的具体文字（OCR 领域）</li>
        <li><b>空间关系</b>："猫在沙发左边还是右边"</li>
        <li><b>精确计数</b>："图中有几只猫"</li>
        <li><b>细节属性</b>：具体色号、面料材质、产品型号</li>
      </ul>
      <p style="margin-top:8px;color:#909399;font-size:12px">"有没有猫"能做，"有几只猫"做不好。</p>
    </div>
  </div>

  <div class="info-cards">
    <div class="info-card">
      <h4><el-icon color="#67C23A"><Histogram /></el-icon> 描述粒度</h4>
      <p>CLIP 的理解分三个层次，<b>物体识别是中粒度强项</b>：</p>
      <ul style="margin-top:8px">
        <li><b>粗粒度（★★★）</b>：场景、媒介、色调</li>
        <li><b>中粒度（★★★）</b>：<b>主体对象识别</b>、风格、动作</li>
        <li><b>细粒度（★☆☆）</b>：品牌型号、精确数量、空间关系</li>
      </ul>
      <p style="margin-top:8px;color:#7C3AED;font-size:12px"><b>搜"咖啡"能找到咖啡图，搜"猫"能找到猫图。</b></p>
    </div>
    <div class="info-card">
      <h4><el-icon color="#409EFF"><Connection /></el-icon> 在本系统中的使用</h4>
      <ul>
        <li><b>上传时</b>：图像编码器提取 512 维向量 → FAISS</li>
        <li><b>搜索时</b>：中文 → 文本编码器 → 向量检索 → Top-K</li>
        <li><b>标签辅助</b>：CLIP 分析结果作为标签建议</li>
        <li><b>去重检测</b>：相似向量检测重复图片</li>
      </ul>
    </div>
    <div class="info-card">
      <h4><el-icon color="#7C3AED"><Star /></el-icon> 模拟数据说明</h4>
      <p>原型中每张素材附带<b>模拟的 CLIP 分析结果</b>：</p>
      <ul style="margin-top:8px">
        <li><b>clipDesc</b>：语义理解描述</li>
        <li><b>clipTags</b>：建议标签</li>
        <li><b>clipStyle</b>：风格分析</li>
        <li><b>搜索匹配理由</b>：语义匹配维度</li>
      </ul>
    </div>
  </div>
</template>
