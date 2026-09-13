import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 15000 })

/** 把后端错误响应转成可读文案 */
function formatError(err) {
  const resp = err.response
  if (!resp) {
    return err.code === 'ECONNABORTED' ? '请求超时，请重试' : '网络异常，请检查后端服务是否已启动'
  }
  const data = resp.data
  if (data && typeof data === 'object') {
    if (data.detail) return String(data.detail)
    // DRF 字段校验错误：{field: ["msg", ...], ...}
    const parts = Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(' ')}`)
    if (parts.length) return parts.join('；')
  }
  return `请求失败（HTTP ${resp.status}）`
}

http.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    ElMessage.error(formatError(err))
    return Promise.reject(err)
  }
)

export default http
