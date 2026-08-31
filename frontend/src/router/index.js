import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('@/views/Landing.vue'),
    meta: { title: 'Nexus Industrial Intelligence' }
  },
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '监控面板' }
      },
      {
        path: 'monitor',
        redirect: '/dashboard'
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue'),
        meta: { title: 'AI智能对话' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router