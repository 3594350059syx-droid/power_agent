import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000
})

service.interceptors.request.use(config => {
  return config
})

service.interceptors.response.use(
  res => {
    const response = res.data

    if (response.success === true) {
      return response
    }

    if (!res.config.silent) {
      ElMessage.error(response.message || '请求失败')
    }
    return Promise.reject(response)
  },
  err => {
    if (!err.config?.silent) {
      ElMessage.error('后端服务异常，请检查 localhost:8000')
    }
    return Promise.reject(err)
  }
)

export default service