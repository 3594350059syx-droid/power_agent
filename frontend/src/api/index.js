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

      // 2. 告警接口（如果有）
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

      // 3. 其他接口：返回空数据，不污染
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