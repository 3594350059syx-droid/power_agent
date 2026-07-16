<template>
  <div class="diagnosis-card">
    <div class="diagnosis-header">
      <span class="diagnosis-icon">📋</span>
      <span class="diagnosis-title">诊断结果</span>
    </div>
    <div class="diagnosis-body">
      <div v-if="data.risk_score !== undefined" class="diagnosis-item">
        <span class="label">风险评分</span>
        <el-tag :type="getRiskType(data.risk_score)" size="small">
          {{ data.risk_score }}分
        </el-tag>
      </div>
      <div v-if="data.anomaly_type" class="diagnosis-item">
        <span class="label">异常类型</span>
        <span class="value">{{ data.anomaly_type }}</span>
      </div>
      <div v-if="data.suggestion" class="diagnosis-item">
        <span class="label">处置建议</span>
        <span class="value">{{ data.suggestion }}</span>
      </div>
      <div v-if="data.details" class="diagnosis-item">
        <span class="label">详情</span>
        <span class="value">{{ data.details }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

const getRiskType = (score) => {
  if (score >= 80) return 'danger'
  if (score >= 50) return 'warning'
  return 'success'
}
</script>

<style scoped>
.diagnosis-card {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
  padding: 12px 16px;
  margin-top: 8px;
}

.diagnosis-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.diagnosis-icon {
  font-size: 18px;
}

.diagnosis-title {
  font-weight: 600;
  font-size: 14px;
  color: #d48806;
}

.diagnosis-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.diagnosis-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 13px;
}

.diagnosis-item .label {
  color: #999;
  min-width: 60px;
  flex-shrink: 0;
}

.diagnosis-item .value {
  color: #333;
  word-break: break-word;
}
</style>