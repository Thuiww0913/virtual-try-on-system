import { createRouter, createWebHistory } from 'vue-router'
import { hasToken } from '../api/client.js'
import { checkAuth } from '../api/admin.js'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '虚拟试衣' },
  },
  {
    path: '/kiosk',
    name: 'kiosk',
    component: () => import('../views/KioskView.vue'),
    meta: { title: '触控模式' },
  },
  {
    path: '/admin/login',
    name: 'admin-login',
    component: () => import('../views/AdminLoginView.vue'),
    meta: { title: '管理员登录' },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/AdminView.vue'),
    meta: { title: '后台管理', requiresAuth: true },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  if (to.meta.title) document.title = `${to.meta.title} · Virtual Try-On`

  if (to.meta.requiresAuth) {
    if (!hasToken()) return { name: 'admin-login', query: { redirect: to.fullPath } }
    const ok = await checkAuth()
    if (!ok) return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
})

export default router
