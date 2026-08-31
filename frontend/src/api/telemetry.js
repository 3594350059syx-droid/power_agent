import request from './index'

const isMock = import.meta.env.VITE_USE_MOCK === 'true'

// 与 data/mock/config.py 保持一致：3 台设备，每台设备 3 个专属测点。
const MOCK_DEVICE_DATA = {
  boiler_002: {
    device_status: { device_id: 'boiler_002', status: 'running' },
    metrics: [
      { key: 'steam_temp', name: '主蒸汽温度', unit: '℃', value: 540, level: 'normal', normal_range: [525, 555] },
      { key: 'steam_pressure', name: '主蒸汽压力', unit: 'MPa', value: 16.7, level: 'normal', normal_range: [16.2, 17.2] },
      { key: 'furnace_temp', name: '炉膛温度', unit: '℃', value: 1200, level: 'normal', normal_range: [1150, 1250] }
    ]
  },
  turbine_003: {
    device_status: { device_id: 'turbine_003', status: 'running' },
    metrics: [
      { key: 'rpm', name: '转速', unit: 'rpm', value: 3000, level: 'normal', normal_range: [2950, 3050] },
      { key: 'bearing_temp', name: '轴承温度', unit: '℃', value: 85, level: 'normal', normal_range: [75, 95] },
      { key: 'vibration', name: '振动', unit: 'mm', value: 0.03, level: 'normal', normal_range: [0.01, 0.05] }
    ]
  },
  generator_004: {
    device_status: { device_id: 'generator_004', status: 'warn' },
    metrics: [
      { key: 'power', name: '有功功率', unit: 'MW', value: 348, level: 'warn', normal_range: [250, 350] },
      { key: 'stator_temp', name: '定子温度', unit: '℃', value: 118, level: 'warn', normal_range: [90, 120] },
      { key: 'reactive_power', name: '无功功率', unit: 'Mvar', value: 72, level: 'warn', normal_range: [30, 70] }
    ]
  }
}

/**
 * 获取单台设备的实时遥测数据。
 * Mock 模式在请求前直接返回本地数据，确保未启动后端时页面仍可用。
 */
export function getLiveTelemetry(deviceId = 'boiler_002') {
  if (isMock) {
    const data = MOCK_DEVICE_DATA[deviceId]
    return Promise.resolve({
      success: true,
      message: 'mock',
      data: data || {
        device_status: { device_id: deviceId, status: 'unknown' },
        metrics: []
      }
    })
  }

  return request({
    url: '/telemetry/live',
    method: 'get',
    params: { device_id: deviceId },
    silent: true
  })
}

/**
 * 并发获取多台设备数据。单个请求失败时仍返回其他设备的结果。
 */
export function getMultipleDevicesTelemetry(deviceIds = ['boiler_002', 'turbine_003', 'generator_004']) {
  return Promise.allSettled(deviceIds.map(getLiveTelemetry)).then(results => (
    results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value
      }
      return {
        success: false,
        message: result.reason?.message || '请求失败',
        data: {
          device_status: { device_id: deviceIds[index], status: 'error' },
          metrics: []
        }
      }
    })
  ))
}

/**
 * 获取历史趋势数据
 * @param {string} deviceId - 设备ID
 * @param {string} parameter - 参数key
 * @param {number} hours - 时间范围（小时）
 */
export function getHistoryTrend(deviceId = 'boiler_002', parameter = 'steam_temp', hours = 24) {
  if (isMock) {
    const now = new Date()
    const timestamps = []
    const values = []
    const anomalyRanges = []

    const deviceData = MOCK_DEVICE_DATA[deviceId]
    if (!deviceData) {
      return Promise.resolve({
        success: true,
        data: { timestamps: [], values: [], anomaly_ranges: [] }
      })
    }

    const metric = deviceData.metrics.find(m => m.key === parameter)
    if (!metric) {
      return Promise.resolve({
        success: true,
        data: { timestamps: [], values: [], anomaly_ranges: [] }
      })
    }

    const normalRange = metric.normal_range || [0, 100]
    const mid = (normalRange[0] + normalRange[1]) / 2
    const range = (normalRange[1] - normalRange[0]) / 2

    for (let i = hours - 1; i >= 0; i--) {
      const t = new Date(now.getTime() - i * 3600000)
      timestamps.push(t.toLocaleString())

      let value = mid + (Math.random() - 0.5) * range * 0.8

      if (Math.random() < 0.1 && values.length > 5) {
        value = normalRange[1] + Math.random() * (normalRange[1] - normalRange[0]) * 0.3
        if (anomalyRanges.length === 0 || anomalyRanges[anomalyRanges.length - 1].end !== timestamps[timestamps.length - 2]) {
          anomalyRanges.push({
            start: timestamps[timestamps.length - 2] || timestamps[0],
            end: timestamps[timestamps.length - 1] || timestamps[0]
          })
        }
      }

      values.push(Math.round(value * 100) / 100)
    }

    return Promise.resolve({
      success: true,
      data: {
        timestamps,
        values,
        anomaly_ranges: anomalyRanges,
        parameter: parameter,
        device_id: deviceId,
        unit: metric.unit || ''
      }
    })
  }

  return request({
    url: '/telemetry/history',
    method: 'get',
    params: { device_id: deviceId, parameter, hours }
  })
}