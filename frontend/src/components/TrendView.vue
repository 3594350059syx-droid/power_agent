<template>
  <div class="trend-view">
    <el-card class="filter-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <el-form-item label="设备">
            <el-select v-model="deviceId" placeholder="选择设备" @change="handleSearch">
              <el-option label="2号机组" value="boiler_002" />
              <el-option label="3号汽轮机" value="turbine_003" />
              <el-option label="4号发电机" value="generator_004" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="参数">
            <ParamSelector v-model="parameter" @update:model-value="handleSearch" />
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
import { ref, computed } from 'vue'
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

const parameterLabel = computed(() => {
  const map = {
    steam_temp: '主蒸汽温度',
    steam_pressure: '主蒸汽压力',
    furnace_temp: '炉膛温度',
    rpm: '转速',
    bearing_temp: '轴承温度',
    vibration: '振动',
    power: '有功功率',
    stator_temp: '定子温度',
    reactive_power: '无功功率'
  }
  return map[parameter.value] || parameter.value
})

const unit = computed(() => {
  const map = {
    steam_temp: '℃',
    steam_pressure: 'MPa',
    furnace_temp: '℃',
    rpm: 'rpm',
    bearing_temp: '℃',
    vibration: 'mm',
    power: 'MW',
    stator_temp: '℃',
    reactive_power: 'Mvar'
  }
  return map[parameter.value] || ''
})

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

handleSearch()
</script>

<style scoped>
.trend-view { padding: 20px; max-width: 1200px; margin: 0 auto; }
.filter-card { margin-bottom: 20px; }
.chart-card { min-height: 460px; }
</style>