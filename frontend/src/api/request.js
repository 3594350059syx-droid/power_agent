import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL:   '/api/v1',
  timeout: 10000
})

service.interceptors.request.use(config => {
  return config
})

service.interceptors.response.use(
  res => {
    const { success, message, data } = res.data
    if (!success) {
      ElMessage.error(message || '请求失败')
      return Promise.reject(res.data)
    }
    return data
  },
  err => {
    const msg = err?.response?.status
      ? `请求失败 (${err.response.status})`
      : '后端服务未启动，请检查 localhost:8000'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default service
