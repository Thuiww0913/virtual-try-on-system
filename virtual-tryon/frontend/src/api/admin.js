/**
 * 管理后台 API
 */
import client, { setToken, clearToken } from './client.js'

export async function login(password) {
  const { data } = await client.post('/api/admin/login', { password })
  if (data.code === 0) setToken(data.data.token)
  return data
}

export async function logout() {
  try { await client.post('/api/admin/logout') } catch (_) { /* ignore */ }
  clearToken()
}

export async function checkAuth() {
  try {
    const { data } = await client.get('/api/admin/check')
    return data.code === 0
  } catch (_) {
    return false
  }
}

export async function adminListClothes() {
  const { data } = await client.get('/api/admin/clothes')
  return data?.data || []
}

export async function uploadClothes(files, { category = 'other', name = '' } = {}) {
  const fd = new FormData()
  for (const f of files) fd.append('files', f)
  fd.append('category', category)
  if (name) fd.append('name', name)
  const { data } = await client.post('/api/admin/clothes', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data?.data || []
}

export async function patchCloth(id, fields) {
  const { data } = await client.patch(`/api/admin/clothes/${id}`, fields)
  return data?.data
}

export async function reorderClothes(ids) {
  const { data } = await client.put('/api/admin/clothes/order', { ids })
  return data
}

export async function deleteCloth(id) {
  const { data } = await client.delete(`/api/admin/clothes/${id}`)
  return data?.data
}
