import request from './index'

// 判断是否 Mock 模式
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

// Mock 数据
const MOCK_DEVICE_DATA = {
  'boiler_002': {
    device_status: { device_id: 'boiler_002', status: 'running' },
    metrics: [
      { key: 'steam_temp', name: '主蒸汽温度', unit: '℃', value: 542, level: 'normal', normal_range: [535, 550] },
      { key: 'steam_pressure', name: '主蒸汽压力', unit: 'MPa', value: 16.5, level: 'normal', normal_range: [15.5, 17.5] },
      { key: 'furnace_temp', name: '炉膛温度', unit: '℃', value: 1120, level: 'normal', normal_range: [1000, 1250] },
      { key: 'vibration', name: '轴承振动', unit: 'mm/s', value: 2.1, level: 'normal', normal_range: [0, 4.5] },
      { key: 'lube_oil_temp', name: '润滑油温度', unit: '℃', value: 42, level: 'normal', normal_range: [35, 50] },
      { key: 'feedwater_flow', name: '给水流量', unit: 't/h', value: 240, level: 'normal', normal_range: [200, 280] }
    ]
  },
  'turbine_003': {
    device_status: { device_id: 'turbine_003', status: 'running' },
    metrics: [
      { key: 'steam_temp', name: '主蒸汽温度', unit: '℃', value: 538, level: 'normal', normal_range: [535, 550] },
      { key: 'steam_pressure', name: '主蒸汽压力', unit: 'MPa', value: 15.8, level: 'normal', normal_range: [15.5, 17.5] },
      { key: 'furnace_temp', name: '炉膛温度', unit: '℃', value: 1080, level: 'normal', normal_range: [1000, 1250] },
      { key: 'vibration', name: '轴承振动', unit: 'mm/s', value: 1.8, level: 'normal', normal_range: [0, 4.5] },
      { key: 'lube_oil_temp', name: '润滑油温度', unit: '℃', value: 38, level: 'normal', normal_range: [35, 50] },
      { key: 'feedwater_flow', name: '给水流量', unit: 't/h', value: 220, level: 'normal', normal_range: [200, 280] }
    ]
  },
  'generator_004': {
    device_status: { device_id: 'generator_004', status: 'warn' },
    metrics: [
      { key: 'steam_temp', name: '主蒸汽温度', unit: '℃', value: 548, level: 'warn', normal_range: [535, 550] },
      { key: 'steam_pressure', name: '主蒸汽压力', unit: 'MPa', value: 17.3, level: 'warn', normal_range: [15.5, 17.5] },
      { key: 'furnace_temp', name: '炉膛温度', unit: '℃', value: 1240, level: 'warn', normal_range: [1000, 1250] },
      { key: 'vibration', name: '轴承振动', unit: 'mm/s', value: 4.2, level: 'warn', normal_range: [0, 4.5] },
      { key: 'lube_oil_temp', name: '润滑油温度', unit: '℃', value: 48, level: 'warn', normal_range: [35, 50] },
      { key: 'feedwater_flow', name: '给水流量', unit: 't/h', value: 195, level: 'warn', normal_range: [200, 280] }
    ]
  }
}

/**
 * 获取实时监控数据
 * @param {string} deviceId - 设备ID
 * @returns {Promise}
 */
export function getLiveTelemetry(deviceId = 'boiler_002') {
  // Mock 模式：直接返回本地数据
  if (isMock) {
    return new Promise((resolve) => {
      const data = MOCK_DEVICE_DATA[deviceId]
      if (data) {
        resolve({
          success: true,
          message: 'ok',
          data: data
        })
      } else {
        // 未知设备返回 unknown 状态
        resolve({
          success: true,
          message: 'ok',
          data: {
            device_status: { device_id: deviceId, status: 'unknown' },
            metrics: []
          }
        })
      }
    })
  }

  // 真实模式：发起请求
  return request({
    url: '/telemetry/live',
    method: 'get',
    params: { device_id: deviceId }
  })
}

/**
 * 获取多台设备实时数据
 * @param {string[]} deviceIds - 设备ID列表
 * @returns {Promise}
 */
export function getMultipleDevicesTelemetry(deviceIds = ['boiler_002', 'turbine_003', 'generator_004']) {
  // 统一使用 Promise.allSettled，Mock 和真实模式共用
  const promises = deviceIds.map(id => getLiveTelemetry(id))
  
  return Promise.allSettled(promises).then(results => {
    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value
      } else {
        console.error(`设备 ${deviceIds[index]} 请求失败:`, result.reason)
        return {
          success: false,
          message: result.reason?.message || '请求失败',
          data: {
            device_status: { device_id: deviceIds[index], status: 'error' },
            metrics: []
          }
        }
      }
    })
  })
}