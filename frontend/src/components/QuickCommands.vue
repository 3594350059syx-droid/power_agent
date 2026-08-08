<template>
  <div class="quick-commands">
    <el-button
      v-for="cmd in commands"
      :key="cmd.label"
      size="small"
      :type="activeCommand === cmd.label ? 'primary' : 'default'"
      @click="handleClick(cmd)"
    >
      {{ cmd.label }}
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  commands: {
    type: Array,
    default: () => [
      { label: '实时监控', value: '查看当前设备实时运行状态' },
      { label: '异常分析', value: '分析当前设备是否存在异常' },
      { label: '趋势预测', value: '预测设备未来运行趋势' },
      { label: '故障诊断', value: '诊断设备故障原因并提供建议' }
    ]
  }
})

const emit = defineEmits(['select'])
const activeCommand = ref('')

const handleClick = (cmd) => {
  activeCommand.value = cmd.label
  emit('select', cmd.value)
}
</script>

<style scoped>
.quick-commands {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0 4px 0;
}

.quick-commands .el-button {
  border-radius: 16px;
  font-size: 13px;
  padding: 4px 16px;
}
</style>