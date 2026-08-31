<template>
  <el-table :data="list" stripe v-loading="loading" style="width: 100%;">
    <el-table-column prop="time" label="时间" width="180" sortable />
    <el-table-column prop="device_name" label="设备" width="120" />
    <el-table-column prop="parameter" label="参数" width="120" />
    <el-table-column prop="alarm_type" label="告警类型" width="140" />
    <el-table-column prop="severity" label="严重等级" width="100">
      <template #default="{ row }">
        <el-tag :type="severityTagMap[row.severity]" size="small">
          {{ severityLabelMap[row.severity] }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="current_value" label="当前值" width="100" />
    <el-table-column prop="threshold" label="阈值" width="100" />
    <el-table-column prop="status" label="状态" width="100">
      <template #default="{ row }">
        <el-tag :type="row.status === 'active' ? 'danger' : 'success'" size="small">
          {{ row.status === 'active' ? '未处理' : '已确认' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="120" fixed="right">
      <template #default="{ row }">
        <el-button v-if="row.status === 'active'" type="primary" size="small" @click="$emit('acknowledge', row.id)">
          确认
        </el-button>
        <span v-else style="color: #999;">已处理</span>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
const severityTagMap = {
  high: 'danger',
  medium: 'warning',
  low: 'info'
}

const severityLabelMap = {
  high: '高',
  medium: '中',
  low: '低'
}

defineProps({
  list: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['acknowledge'])
</script>