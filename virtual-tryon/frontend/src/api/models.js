/**
 * 公开模特(人像)相册 API —— 与 clothes.js 结构对称
 * 模特没有分类(category),数据更简单。
 */
import client from './client.js'

export async function listModels() {
  const { data } = await client.get('/api/models')
  return data?.data || []
}
