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
    default: () => []
  }
})

defineEmits(['update:modelValue'])
</script>