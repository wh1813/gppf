// 文件路径: frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/chart/000001' // 默认跳转到平安银行的分析页
  },
  {
    path: '/chart/:symbol',
    name: 'ChartAnalysis',
    // 懒加载页面组件
    component: () => import('@/views/chart/ChartAnalysis.vue')
  },
  {
    path: '/pool',
    name: 'PoolManager',
    component: () => import('@/views/pool/PoolManager.vue')
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