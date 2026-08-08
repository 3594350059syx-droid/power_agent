import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

service.interceptors.request.use(config => {
  return config
})

service.interceptors.response.use(
  res => {
    const response = res.data

    // Mock 模式：按接口路径返回不同数据
    if (import.meta.env.VITE_USE_MOCK === 'true') {
      const url = res.config.url || ''

      // 1. AI 对话接口
      if (url.includes('/agent/chat')) {
        return {
          success: true,
          message: 'mock',
          data: {
            reply: '【Mock 模式】已收到您的问题，请配置真实 DeepSeek API Key',
            diagnosis: null
          }
        }
      }

      // 2. 遥测数据接口（监控面板用）- 与后端格式对齐
      if (url.includes('/telemetry/live')) {
        const deviceId = res.config.params?.device_id || 'boiler_002'

        const deviceDataMap = {
          'boiler_002': {
            device_status: { device_id: 'boiler_002', status: 'running' },
            metrics: [
              { key: 'steam_temp', name: '主蒸汽温度', unit: '℃', value: 72, level: 'normal' },
              { key: 'steam_pressure', name: '主蒸汽压力', unit: 'MPa', value: 3.2, level: 'normal' },
              { key: 'vibration', name: '轴承振动', unit: 'mm/s', value: 0.8, level: 'normal' },
              { key: 'power', name: '功率', unit: 'MW', value: 2847, level: 'normal' }
            ]
          },
          'turbine_003': {
            device_status: { device_id: 'turbine_003', status: 'running' },
            metrics: [
              { key: 'steam_temp', name: '主蒸汽温度', unit: '℃', value: 68, level: 'normal' },
              { key: 'steam_pressure', name: '主蒸汽压力', unit: 'MPa', value: 2.9, level: 'normal' },
              { key: 'vibration', name: '轴承振动', unit: 'mm/s', value: 0.5, level: 'normal' },
              { key: 'power', name: '功率', unit: 'MW', value: 3201, level: 'normal' }
            ]
          },
          'generator_004': {
            device_status: { device_id: 'generator_004', status: 'warning' },
            metrics: [
              { key: 'steam_temp', name: '主蒸汽温度', unit: '℃', value: 82, level: 'warning' },
              { key: 'steam_pressure', name: '主蒸汽压力', unit: 'MPa', value: 3.8, level: 'warning' },
              { key: 'vibration', name: '轴承振动', unit: 'mm/s', value: 1.2, level: 'warning' },
              { key: 'power', name: '功率', unit: 'MW', value: 1523, level: 'warning' }
            ]
          }
        }

        const data = deviceDataMap[deviceId] || deviceDataMap['boiler_002']
        return {
          success: true,
          message: 'ok',
          data: data
        }
      }

      // 3. 告警接口（如果有）
      if (url.includes('/alarm')) {
        return {
          success: true,
          data: {
            alarms: [
              { id: 1, level: 'warning', message: '2号机组温度偏高' }
            ]
          }
        }
      }

      // 4. 其他接口：返回空数据，不污染
      return {
        success: true,
        data: {}
      }
    }

    // 真实后端响应
    if (response.success === true) {
      return response
    } else {
      ElMessage.error(response.message || '请求失败')
      return Promise.reject(response)
    }
  },
  err => {
    ElMessage.error('后端服务异常，请检查 localhost:8000')
    return Promise.reject(err)
  }
)

export default service