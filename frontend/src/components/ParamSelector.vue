<template>
  <el-select :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" placeholder="选择参数">
    <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value" />
  </el-select>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  options: {
    type: Array,
    default: () => [
      { label: '主蒸汽温度', value: 'steam_temp' },
      { label: '主蒸汽压力', value: 'steam_pressure' },
      { label: '炉膛温度', value: 'furnace_temp' },
      { label: '转速', value: 'rpm' },
      { label: '轴承温度', value: 'bearing_temp' },
      { label: '振动', value: 'vibration' },
      { label: '有功功率', value: 'power' },
      { label: '定子温度', value: 'stator_temp' },
      { label: '无功功率', value: 'reactive_power' }
    ]
  }
})

defineEmits(['update:modelValue'])
</script>