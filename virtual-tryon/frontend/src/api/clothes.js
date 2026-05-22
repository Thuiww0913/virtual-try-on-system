/**
 * 公开衣服 API（前台 Dock 使用）
 * 分类与 OOTDiffusion 标准对齐：
 *   upperbody = 0 (上半身)
 *   lowerbody = 1 (下半身)
 *   dress     = 2 (连衣裙)
 */
import client from './client.js'

export async function listClothes(category) {
  const params = category && category !== 'all' ? { category } : {}
  const { data } = await client.get('/api/clothes', { params })
  return data?.data || []
}

/* ── 分类常量 ──────────────────────────────────────────────── */
export const CATEGORIES = [
  { value: 'all',       label: '全部',   icon: '✦' },
  { value: 'upperbody', label: '上半身', icon: '👕' },
  { value: 'lowerbody', label: '下半身', icon: '👖' },
  { value: 'dress',     label: '连衣裙', icon: '👗' },
]

export const CATEGORY_LABEL = {
  upperbody: '上半身',
  lowerbody: '下半身',
  dress:     '连衣裙',
}

export const DEFAULT_CATEGORY = 'upperbody'
