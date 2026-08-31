<template>
  <div class="trend-view">
    <el-card class="filter-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <el-form-item label="设备">
            <el-select v-model="deviceId" placeholder="选择设备" @change="handleDeviceChange">
              <el-option label="2号锅炉" value="boiler_002" />
              <el-option label="3号汽轮机" value="turbine_003" />
              <el-option label="4号发电机" value="generator_004" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="参数">
            <ParamSelector :model-value="parameter" :options="parameterOptions" @update:model-value="handleParameterChange" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="时间范围">
            <TimeRangePicker v-model="hours" @update:model-value="handleSearch" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="chart-card" v-loading="loading">
      <TrendChart
        :data="chartData"
        :x-data="chartXData"
        :parameter="parameterLabel"
        :unit="unit"
        :anomaly-ranges="anomalyRanges"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import TrendChart from '@/components/TrendChart.vue'
import TimeRangePicker from '@/components/TimeRangePicker.vue'
import ParamSelector from '@/components/ParamSelector.vue'
import { getHistoryTrend } from '@/api/telemetry'

const deviceId = ref('boiler_002')
const parameter = ref('steam_temp')
const hours = ref(24)
const loading = ref(false)

const chartData = ref([])
const chartXData = ref([])
const anomalyRanges = ref([])

const metricOptionsByDevice = {
  boiler_002: [
    { label: '主蒸汽温度', value: 'steam_temp', unit: '℃' },
    { label: '主蒸汽压力', value: 'steam_pressure', unit: 'MPa' },
    { label: '炉膛温度', value: 'furnace_temp', unit: '℃' }
  ],
  turbine_003: [
    { label: '转速', value: 'rpm', unit: 'rpm' },
    { label: '轴承温度', value: 'bearing_temp', unit: '℃' },
    { label: '振动', value: 'vibration', unit: 'mm' }
  ],
  generator_004: [
    { label: '有功功率', value: 'power', unit: 'MW' },
    { label: '定子温度', value: 'stator_temp', unit: '℃' },
    { label: '无功功率', value: 'reactive_power', unit: 'Mvar' }
  ]
}

const parameterOptions = computed(() => metricOptionsByDevice[deviceId.value] || [])
const selectedMetric = computed(() => parameterOptions.value.find(item => item.value === parameter.value))
const parameterLabel = computed(() => selectedMetric.value?.label || parameter.value)
const unit = computed(() => selectedMetric.value?.unit || '')

const handleDeviceChange = () => {
  if (!parameterOptions.value.some(item => item.value === parameter.value)) {
    parameter.value = parameterOptions.value[0]?.value || ''
  }
  handleSearch()
}

const handleParameterChange = (value) => {
  parameter.value = value
  handleSearch()
}

const handleSearch = async () => {
  if (!deviceId.value || !parameter.value) {
    ElMessage.warning('请选择设备和参数')
    return
  }

  loading.value = true
  try {
    const res = await getHistoryTrend(deviceId.value, parameter.value, hours.value)

    if (res.success && res.data) {
      chartData.value = res.data.values || []
      chartXData.value = res.data.timestamps || []
      anomalyRanges.value = res.data.anomaly_ranges || []
    } else {
      ElMessage.error(res.message || '获取历史数据失败')
    }
  } catch (error) {
    console.error('获取历史数据失败:', error)
    ElMessage.error('获取历史数据失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  deviceId.value = 'boiler_002'
  parameter.value = 'steam_temp'
  hours.value = 24
  handleSearch()
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.trend-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.filter-card {
  margin-bottom: 20px;
}
.chart-card {
  min-height: 460px;
}
</style>
