import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      redirect: '/assets',
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录', guestOnly: true },
    },
    {
      path: '/assets',
      name: 'Assets',
      component: () => import('@/views/AssetsView.vue'),
      meta: { title: '素材库' },
    },
    {
      path: '/collections',
      name: 'Collections',
      component: () => import('@/views/CollectionsView.vue'),
      meta: { title: '分组管理' },
    },
    {
      path: '/collection/:id',
      name: 'CollectionDetail',
      component: () => import('@/views/CollectionDetailView.vue'),
      meta: { title: '分组详情' },
    },
    {
      path: '/search',
      name: 'Search',
      component: () => import('@/views/SearchView.vue'),
      meta: { title: '以文搜图' },
    },
    {
      path: '/upload',
      name: 'Upload',
      component: () => import('@/views/UploadView.vue'),
      meta: { title: '上传素材', requiresAuth: true, minRole: 'editor' },
    },
    {
      path: '/clip-info',
      name: 'ClipInfo',
      component: () => import('@/views/ClipInfoView.vue'),
      meta: { title: 'CLIP 能力说明' },
    },
    {
      path: '/share-manage',
      name: 'ShareManage',
      component: () => import('@/views/ShareManageView.vue'),
      meta: { title: '分享管理', requiresAuth: true, minRole: 'editor' },
    },
    {
      path: '/audit',
      name: 'Audit',
      component: () => import('@/views/AuditView.vue'),
      meta: { title: '审计日志', requiresAuth: true, minRole: 'admin' },
    },
    {
      path: '/asset/:id',
      name: 'AssetDetail',
      component: () => import('@/views/AssetDetailView.vue'),
      meta: { title: '素材详情' },
    },
  ],
})

// 全局路由守卫
router.beforeEach((to, _from, next) => {
  document.title = (to.meta.title as string) || 'CLIP-Image 素材库'

  const authStore = useAuthStore()

  // 仅访客可访问的页面（如登录页）
  if (to.meta.guestOnly && authStore.isLoggedIn) {
    return next('/assets')
  }

  // 需要登录的页面
  if (to.meta.requiresAuth && authStore.isGuest) {
    return next('/login')
  }

  // 需要特定角色的页面
  if (to.meta.minRole) {
    const roleHierarchy: Record<string, number> = { admin: 3, editor: 2, guest: 1 }
    const required = roleHierarchy[to.meta.minRole as string] || 0
    const current = roleHierarchy[authStore.role] || 0
    if (current < required) {
      return next('/login')
    }
  }

  next()
})

export default router
