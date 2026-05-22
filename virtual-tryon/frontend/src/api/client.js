/**
 * 公共 axios 实例
 * - 自动注入 Authorization 头（如果 localStorage 中存在 admin_token）
 * - 401 时清除 token 并跳转 /admin/login
 */
import axios from 'axios'

const TOKEN_KEY = 'vt_admin_token'

export const getToken    = () => localStorage.getItem(TOKEN_KEY) || ''
export const setToken    = (t) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken  = ()  => localStorage.removeItem(TOKEN_KEY)
export const hasToken    = ()  => !!getToken()

const client = axios.create({
  baseURL: '',
  timeout: 60_000,
})

client.interceptors.request.use((config) => {
  const t = getToken()
  if (t) config.headers.Authorization = `Bearer ${t}`
  return config
})

client.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err?.response?.status === 401) {
      clearToken()
      // 仅在管理后台路由内时才自动跳转，避免影响公开接口
      if (location.pathname.startsWith('/admin') &&
          !location.pathname.endsWith('/admin/login')) {
        location.href = '/admin/login'
      }
    }
    return Promise.reject(err)
  },
)

export default client
