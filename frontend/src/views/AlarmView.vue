<template>
  <div class="alarm-view">
    <el-card class="filter-card">
      <AlarmFilter
        v-model:severity="severity"
        v-model:sort="sort"
        @search="handleSearch"
        @reset="handleReset"
      />
    </el-card>

    <el-card class="table-card">
      <AlarmTable :list="alarmList" :loading="loading" @acknowledge="handleAcknowledge" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AlarmFilter from '@/components/AlarmFilter.vue'
import AlarmTable from '@/components/AlarmTable.vue'
import { getAlarmList, acknowledgeAlarm } from '@/api/alarm'

const severity = ref('all')
const sort = ref('time_desc')
const alarmList = ref([])
const loading = ref(false)

const handleSearch = async () => {
  loading.value = true
  try {
    const res = await getAlarmList(severity.value, sort.value)
    if (res.success) {
      alarmList.value = res.data?.alarms || []
    } else {
      ElMessage.error(res.message || '获取告警列表失败')
    }
  } catch (error) {
    console.error('获取告警列表失败:', error)
    ElMessage.error('获取告警列表失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  severity.value = 'all'
  sort.value = 'time_desc'
  handleSearch()
}

const handleAcknowledge = async (alarmId) => {
  try {
    const res = await acknowledgeAlarm(alarmId)
    if (res.success) {
      ElMessage.success('告警已确认')
      handleSearch()
    } else {
      ElMessage.error(res.message || '确认失败')
    }
  } catch (error) {
    console.error('确认告警失败:', error)
    ElMessage.error('确认告警失败，请检查后端服务')
  }
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.alarm-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  min-height: 400px;
}
</style>