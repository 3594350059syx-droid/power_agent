<template>
  <div class="alarm-filter">
    <el-select :model-value="severity" @update:model-value="$emit('update:severity', $event)" placeholder="严重等级" clearable>
      <el-option label="全部" value="all" />
      <el-option label="高" value="high" />
      <el-option label="中" value="medium" />
      <el-option label="低" value="low" />
    </el-select>

    <el-select :model-value="sort" @update:model-value="$emit('update:sort', $event)" placeholder="排序" style="margin-left: 12px;">
      <el-option label="最新优先" value="time_desc" />
      <el-option label="最早优先" value="time_asc" />
    </el-select>

    <el-button type="primary" style="margin-left: 12px;" @click="$emit('search')">查询</el-button>
    <el-button @click="$emit('reset')">重置</el-button>
  </div>
</template>

<script setup>
defineProps({
  severity: { type: String, default: 'all' },
  sort: { type: String, default: 'time_desc' }
})

defineEmits(['update:severity', 'update:sort', 'search', 'reset'])
</script>

<style scoped>
.alarm-filter {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
</style>