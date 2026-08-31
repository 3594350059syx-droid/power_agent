<template>
  <div ref="chartRef" class="trend-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let chart = null

const handleResize = () => chart?.resize()

const props = defineProps({
  data: { type: Array, default: () => [] },
  xData: { type: Array, default: () => [] },
  parameter: { type: String, default: '' },
  unit: { type: String, default: '' },
  anomalyRanges: { type: Array, default: () => [] }
})

const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateChart()
  window.addEventListener('resize', handleResize)
}

const updateChart = () => {
  if (!chart) return

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        if (!p) return ''
        return `${p.axisValue}<br/>${props.parameter}: ${p.value} ${props.unit}`
      }
    },
    grid: { left: 60, right: 30, top: 30, bottom: 60 },
    xAxis: {
      type: 'category',
      data: props.xData,
      boundaryGap: false,
      axisLabel: { rotate: 30, interval: Math.max(0, Math.floor(props.xData.length / 20)) }
    },
    yAxis: {
      type: 'value',
      name: props.unit ? `${props.parameter} (${props.unit})` : props.parameter
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, height: 30 }
    ],
    series: [{
      name: props.parameter || '趋势',
      type: 'line',
      data: props.data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { color: '#1890ff', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
          ]
        }
      },
      markArea: props.anomalyRanges.length > 0 ? {
        silent: true,
        data: props.anomalyRanges.map(range => [
          { xAxis: range.start, itemStyle: { color: 'rgba(255, 0, 0, 0.25)' } },
          { xAxis: range.end, itemStyle: { color: 'rgba(255, 0, 0, 0.25)' } }
        ])
      } : undefined
    }]
  }

  chart.setOption(option)
}

watch(() => [props.data, props.xData, props.parameter, props.unit, props.anomalyRanges], () => {
  nextTick(() => updateChart())
}, { deep: true })

onMounted(() => {
  nextTick(() => initChart())
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.trend-chart { width: 100%; height: 420px; }
</style>