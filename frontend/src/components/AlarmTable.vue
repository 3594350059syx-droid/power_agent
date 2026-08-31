<template>
  <el-table :data="list" stripe v-loading="loading" style="width: 100%;">
    <el-table-column prop="triggered_at" label="时间" width="180" sortable>
      <template #default="{ row }">{{ formatTime(row.triggered_at) }}</template>
    </el-table-column>
    <el-table-column prop="device_name" label="设备" width="120" />
    <el-table-column prop="parameter_name" label="参数" width="120" />
    <el-table-column prop="alarm_type" label="告警类型" width="140" />
    <el-table-column prop="severity" label="严重等级" width="100">
      <template #default="{ row }">
        <el-tag :class="`severity-${row.severity}`" effect="dark" size="small">
          {{ severityLabelMap[row.severity] }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="current_value" label="当前值" width="100" />
    <el-table-column prop="threshold_value" label="阈值" width="100" />
    <el-table-column prop="status" label="状态" width="100">
      <template #default="{ row }">
        <el-tag :type="row.status === 'pending' ? 'danger' : 'success'" size="small">
          {{ row.status === 'pending' ? '未处理' : '已确认' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="120" fixed="right">
      <template #default="{ row }">
        <el-button v-if="row.status === 'pending'" type="primary" size="small" @click="$emit('acknowledge', row.id)">
          确认
        </el-button>
        <span v-else style="color: #999;">已处理</span>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
const severityLabelMap = {
  high: '高',
  medium: '中',
  low: '低'
}

const formatTime = (value) => {
  if (!value) return '-'
  const time = new Date(value)
  return Number.isNaN(time.getTime()) ? value : time.toLocaleString('zh-CN', { hour12: false })
}

defineProps({
  list: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['acknowledge'])
</script>

<style scoped>
.severity-high {
  --el-tag-bg-color: #dc2626;
  --el-tag-border-color: #dc2626;
  --el-tag-text-color: #fff;
}

.severity-medium {
  --el-tag-bg-color: #ea580c;
  --el-tag-border-color: #ea580c;
  --el-tag-text-color: #fff;
}

.severity-low {
  --el-tag-bg-color: #eab308;
  --el-tag-border-color: #eab308;
  --el-tag-text-color: #422006;
}
</style>