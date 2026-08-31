<template>
  <el-select :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" placeholder="选择时间范围">
    <el-option label="过去6小时" :value="6" />
    <el-option label="过去12小时" :value="12" />
    <el-option label="过去24小时" :value="24" />
    <el-option label="过去7天" :value="168" />
  </el-select>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Number,
    default: 24
  }
})

defineEmits(['update:modelValue'])
</script>