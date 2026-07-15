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
    if (import.meta.env.VITE_USE_MOCK === 'true') {
    const mockData = {
        success: true,
        message: '操作成功',
        data: {
            "dialogue": "这里是模拟的对话内容"
        }
    }
    return mockData
}
    const { success, message, data } = res.data
    if (!success) {
      ElMessage.error(message || '请求失败')
      return Promise.reject(res.data)
    }
    return data
  },
  err => {
    ElMessage.error('后端服务异常，请检查localhost:8080')
    return Promise.reject(err)
  }
)

export default service