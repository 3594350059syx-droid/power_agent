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