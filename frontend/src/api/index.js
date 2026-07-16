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
    // Mock 模式
    if (import.meta.env.VITE_USE_MOCK === 'true') {
      const mockData = {
        success: true,
        message: '操作成功',
        data: {
          reply: '这里是模拟的对话内容'
        }
      }
      return mockData
    }

    // 真实后端响应
    const response = res.data
    // 后端返回格式：{ success: true, message: 'ok', data: { reply: '...' } }
    if (response.success === true) {
      return response  // 直接返回完整响应
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