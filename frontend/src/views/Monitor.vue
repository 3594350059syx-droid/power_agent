<template>
  <div class="monitor">
    <h2>设备实时监控面板</h2>
    <el-card v-if="deviceData">
      <h3>设备ID：{{ deviceData.device_status?.device_id }}</h3>
      <div class="metrics">
        <div
          v-for="item in deviceData.metrics"
          :key="item.key"
          :class="statusClass(item.level)"
        >
          {{ item.name }}：{{ item.value }} {{ item.unit }}
        </div>
      </div>
    </el-card>
    <el-empty v-else description="加载中..." />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getLiveTelemetry } from '@/api/telemetry'

const deviceData = ref(null)
let timer = null

const statusClass = (level) => {
  if (level === 'normal') return 'green'
  if (level === 'warn') return 'yellow'
  return 'red'
}

const refresh = async () => {
  try {
    deviceData.value = await getLiveTelemetry()
  } catch (err) {
    console.log('监控接口暂未就绪，使用Mock调试')
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 3000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.monitor {
  width: 900px;
  margin: 30px auto;
}
.metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-top: 20px;
}
.green {
  background: #e6f7e6;
  color: #009944;
  padding: 10px;
  border-radius: 6px;
}
.yellow {
  background: #fffbe6;
  color: #faad14;
  padding: 10px;
  border-radius: 6px;
}
.red {
  background: #fff2f0;
  color: #f5222d;
  padding: 10px;
  border-radius: 6px;
}
</style>
