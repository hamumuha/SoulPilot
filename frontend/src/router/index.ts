import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/pages/LoginView.vue') },
  {
    path: '/',
    name: 'soul',
    component: () => import('@/pages/SoulJourneyView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat/:conversationId?',
    name: 'chat',
    component: () => import('@/components/ChatPanel.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/components/SettingsPanel.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login' }
  }
  if (to.name === 'login' && auth.isLoggedIn) {
    return { name: 'soul' }
  }
  return true
})

export default router
