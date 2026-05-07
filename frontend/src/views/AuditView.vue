<script setup lang="ts">
const auditLogs = [
  { time:'2026-05-07 14:32:10', user:'小明', action:'下载', target:'科技感蓝色背景图', ip:'192.168.1.101' },
  { time:'2026-05-07 13:15:22', user:'小红', action:'上传', target:'产品白底图系列-A款', ip:'192.168.1.102' },
  { time:'2026-05-07 11:08:45', user:'运营部', action:'分享', target:'双十一促销海报', ip:'192.168.1.150' },
  { time:'2026-05-07 09:22:30', user:'设计部', action:'编辑', target:'App登录页设计稿', ip:'192.168.1.120' },
  { time:'2026-05-06 16:45:11', user:'小明', action:'下载', target:'春季新品发布海报', ip:'192.168.1.101' },
  { time:'2026-05-06 15:30:05', user:'小红', action:'上传', target:'2026年会大合影', ip:'192.168.1.102' },
  { time:'2026-05-06 14:12:33', user:'设计部', action:'版本回滚', target:'春季新品发布海报', ip:'192.168.1.120' },
  { time:'2026-05-06 10:08:17', user:'管理员_张伟', action:'删除', target:'废弃设计稿-旧版', ip:'192.168.1.1' },
]

function actionType(a: string) {
  const m: Record<string, string> = { '上传':'success', '下载':'', '分享':'warning', '编辑':'info', '删除':'danger', '版本回滚':'info' }
  return m[a] || ''
}
</script>

<template>
  <h2 style="font-size:18px;margin-bottom:16px">审计日志</h2>
  <div class="audit-table">
    <el-table :data="auditLogs" stripe>
      <el-table-column prop="time" label="时间" width="170" />
      <el-table-column prop="user" label="用户" width="100" />
      <el-table-column prop="action" label="操作" width="100">
        <template #default="{ row }">
          <el-tag :type="actionType(row.action)" size="small">{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target" label="目标素材" />
      <el-table-column prop="ip" label="IP 地址" width="140" />
    </el-table>
  </div>
</template>
