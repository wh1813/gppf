import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/chart/002202' // 默认打开终端
  },
  {
    path: '/chart/:symbol',
    name: 'ChartAnalysis',
    component: () => import('@/views/chart/ChartAnalysis.vue') // 三栏一体化核心组件
  },
  {
    path: '/console',
    name: 'AnalysisConsole',
    component: () => import('@/views/analysis/AnalysisConsole.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router