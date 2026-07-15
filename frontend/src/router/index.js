import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        redirect: '/monitor'
      },
      {
        path: '/monitor',
        name: 'Monitor',
        component: () => import('@/views/Monitor.vue'),
        meta: { title: '监控面板' }
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
