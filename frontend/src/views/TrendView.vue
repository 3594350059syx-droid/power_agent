cat > src/views/TrendView.vue << 'EOF'
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
            <el-select v-model="parameter" placeholder="选择参数" @change="handleSearch">
              <el-option label="主蒸汽温度" value="steam_temp" />
              <el-option label="主蒸汽压力" value="steam_pressure" />
              <el-option label="炉膛温度" value="furnace_temp" />
              <el-option label="转速" value="rpm" />
              <el-option label="轴承温度" value="bearing_temp" />
              <el-option label="振动" value="vibration" />
              <el-option label="有功功率" value="power" />
              <el-option label="定子温度" value="stator_temp" />
              <el-option label="无功功率" value="reactive_power" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="时间范围">
            <el-select v-model="hours" @change="handleSearch">
              <el-option label="过去6小时" :value="6" />
              <el-option label="过去12小时" :value="12" />
              <el-option label="过去24小时" :value="24" />
              <el-option label="过去7天" :value="168" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="chart-card" v-loading="loading">
      <div style="height:420px;display:flex;align-items:center;justify-content:center;color:#999;">
        图表组件待接入
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const deviceId = ref('boiler_002')
const parameter = ref('steam_temp')
const hours = ref(24)
const loading = ref(false)

const handleSearch = () => {
  ElMessage.info('查询功能开发中')
}

const handleReset = () => {
  deviceId.value = 'boiler_002'
  parameter.value = 'steam_temp'
  hours.value = 24
}
</script>

<style scoped>
.trend-view { padding: 20px; max-width: 1200px; margin: 0 auto; }
.filter-card { margin-bottom: 20px; }
.chart-card { min-height: 460px; }
</style>
EOF