import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 15000 })

http.interceptors.response.use(
  (resp) => resp.data,
  (err) => Promise.reject(err.response?.data || err)
)

export default http
