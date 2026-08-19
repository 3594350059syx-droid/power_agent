<template>
  <div class="dashboard-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2>📊 设备实时监控面板</h2>
        <el-tag :type="isConnected ? 'success' : 'danger'" size="small">
          {{ isConnected ? '已连接' : '离线' }}
        </el-tag>
      </div>
      <div class="header-right">
        <span class="refresh-info">
          ⏱ 上次刷新：{{ lastUpdateTime || '--' }}
          <span class="refresh-interval">｜每 3 秒自动刷新</span>
        </span>
        <el-button size="small" :loading="isLoading" @click="refreshData">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 加载骨架 -->
    <div v-if="isLoading && devices.length === 0" class="loading-skeleton">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 离线提示 -->
    <el-alert
      v-else-if="!isConnected"
      title="⚠️ 接口连接失败，请检查后端服务是否正常运行"
      type="error"
      show-icon
      :closable="false"
      class="offline-alert"
    />

    <!-- 设备卡片网格 -->
    <el-row v-else :gutter="20" class="device-grid">
      <el-col
        v-for="device in devices"
        :key="device.deviceId"
        :xs="24"
        :sm="12"
        :lg="8"
      >
        <DeviceCard
          :device-id="device.deviceId"
          :device-name="device.deviceName"
          :device-status="device.deviceStatus"
          :metrics="device.metrics"
          :update-time="lastUpdateTime"
        />
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty v-if="!isLoading && devices.length === 0" description="暂无设备数据" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import DeviceCard from '@/components/DeviceCard.vue'
import { getMultipleDevicesTelemetry } from '@/api/telemetry'

// ============ 设备配置 ============
const DEVICE_CONFIG = [
  { id: 'boiler_002', name: '2号机组' },
  { id: 'turbine_003', name: '3号汽轮机' },
  { id: 'generator_004', name: '4号发电机' }
]

// ============ 状态 ============
const devices = ref([])
const isLoading = ref(false)
const isConnected = ref(true)
const lastUpdateTime = ref('')
let refreshTimer = null

// ============ 数据处理 ============
const processDeviceData = (deviceId, deviceName, response) => {
  const data = response?.data || response
  const metrics = data?.metrics || []
  const deviceStatus = data?.device_status?.status || 'running'

  return {
    deviceId,
    deviceName,
    deviceStatus,
    metrics: metrics.map(m => ({
      ...m,
      level: m.level || 'normal'
    }))
  }
}

// ============ 获取数据 ============
const fetchAllDevices = async () => {
  if (isLoading.value) return
  isLoading.value = true

  try {
    const ids = DEVICE_CONFIG.map(d => d.id)
    const results = await getMultipleDevicesTelemetry(ids)

    const parsedDevices = results.map((res, index) => {
      const config = DEVICE_CONFIG[index]
      return processDeviceData(
        config.id,
        config.name,
        res
      )
    })

    devices.value = parsedDevices
    isConnected.value = true
    lastUpdateTime.value = new Date().toLocaleTimeString()

  } catch (error) {
    console.error('获取监控数据失败:', error)
    isConnected.value = false
    if (devices.value.length === 0) {
      ElMessage.error('连接监控服务失败，请检查后端是否运行')
    }
  } finally {
    isLoading.value = false
  }
}

// ============ 刷新控制 ============
const refreshData = async () => {
  await fetchAllDevices()
}

const startPolling = () => {
  if (refreshTimer) clearInterval(refreshTimer)
  refreshTimer = setInterval(() => {
    fetchAllDevices()
  }, 3000)
}

const stopPolling = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// ============ 生命周期 ============
onMounted(async () => {
  await refreshData()
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: #999;
}

.refresh-interval {
  color: #bfbfbf;
}

.loading-skeleton {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
}

.offline-alert {
  margin-bottom: 20px;
}

.device-grid {
  margin-top: 8px;
}
</style>