import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '运行总览' } },
  { path: '/stations', name: 'stations', component: () => import('../views/Stations.vue'), meta: { title: '电站管理' } },
  { path: '/stations/:id', name: 'station-detail', component: () => import('../views/StationDetail.vue'), meta: { title: '电站详情' } },
  { path: '/alarms', name: 'alarms', component: () => import('../views/Alarms.vue'), meta: { title: '异常告警' } },
  { path: '/inspections', name: 'inspections', component: () => import('../views/Inspections.vue'), meta: { title: '巡检工单' } },
  { path: '/cleanings', name: 'cleanings', component: () => import('../views/Cleaning.vue'), meta: { title: '清洗计划' } },
  { path: '/defects', name: 'defects', component: () => import('../views/Defects.vue'), meta: { title: '消缺记录' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
