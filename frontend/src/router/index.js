import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '监控面板' }
      },
      {
        path: '/monitor',
        redirect: '/dashboard'
      },
      {
        path: '/trend',
        name: 'Trend',
        component: () => import('@/views/TrendView.vue'),
        meta: { title: '趋势分析' }
      },
      {
        path: '/alarm',
        name: 'Alarm',
        component: () => import('@/views/AlarmView.vue'),
        meta: { title: '告警中心' }
      },
      {
        path: '/chat',
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