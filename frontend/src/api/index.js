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

      // 2. 遥测数据接口（监控面板用）
      if (url.includes('/telemetry/live')) {
        return {
          success: true,
          data: [
            {
              device_id: 'dev_001',
              device_name: '2号机组',
              temperature: 72,
              pressure: 3.2,
              vibration: 0.8,
              power: 2847,
              status: 'normal'
            },
            {
              device_id: 'dev_002',
              device_name: '3号机组',
              temperature: 68,
              pressure: 2.9,
              vibration: 0.5,
              power: 3201,
              status: 'normal'
            },
            {
              device_id: 'dev_003',
              device_name: '4号机组',
              temperature: 82,
              pressure: 3.8,
              vibration: 1.2,
              power: 1523,
              status: 'warn'
            }
          ]
        }
      }

      // 3. 告警接口（如果有）
      if (url.includes('/alarm')) {
        return {
          success: true,
          data: {
            alarms: [
              { id: 1, level: 'warn', message: '2号机组温度偏高' }
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