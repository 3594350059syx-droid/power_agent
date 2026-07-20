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

    // Mock 模式：只对 chat 接口生效
    if (import.meta.env.VITE_USE_MOCK === 'true') {
      const url = res.config.url || ''
      if (url.includes('/agent/chat')) {
        return {
          success: true,
          message: 'mock',
          data: {
            reply: '【Mock 模式】已收到您的问题，请配置真实 DeepSeek API Key'
          }
        }
      }
      // 其他接口（telemetry / alarm / report）正常返回，不污染
      return response
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