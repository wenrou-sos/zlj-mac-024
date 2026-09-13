<template>
  <div v-loading="loading">
    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div>
              <div class="stat-label">{{ c.label }}</div>
              <div class="stat-value">{{ c.value }}<span class="stat-unit">{{ c.unit }}</span></div>
            </div>
            <div class="stat-icon" :style="{ background: c.bg }">
              <el-icon :size="26" :color="c.color"><component :is="c.icon" /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 发电趋势 + 设备状态 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header><span class="card-title">近 30 天全场发电趋势</span></template>
          <div ref="trendRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header><span class="card-title">设备状态分布（共 {{ data.device_total || 0 }} 台）</span></template>
          <div ref="deviceRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 告警统计 + 最新告警 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header><span class="card-title">活跃告警级别分布</span></template>
          <div ref="alarmRef" class="chart-box" style="height: 260px"></div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">最新活跃告警</span>
              <el-button text type="primary" @click="$router.push('/alarms')">全部告警 →</el-button>
            </div>
          </template>
          <el-table :data="data.recent_alarms || []" size="small" style="height: 260px">
            <el-table-column prop="created_at" label="时间" width="140" />
            <el-table-column prop="station_name" label="电站" width="150" show-overflow-tooltip />
            <el-table-column label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="alarmLevel[row.level].type" size="small">{{ alarmLevel[row.level].label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="告警内容" show-overflow-tooltip />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="alarmStatus[row.status].type" size="small" effect="plain">{{ alarmStatus[row.status].label }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 待办事项 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8" v-for="t in todos" :key="t.label">
        <el-card shadow="hover" class="todo-card" @click="$router.push(t.path)">
          <div class="todo-inner">
            <el-icon :size="30" :color="t.color"><component :is="t.icon" /></el-icon>
            <div class="todo-text">
              <div class="todo-num">{{ t.value }}</div>
              <div class="todo-label">{{ t.label }}</div>
            </div>
            <el-icon class="todo-arrow"><ArrowRight /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '../api'
import { useChart } from '../utils/chart'
import { alarmLevel, alarmStatus, fmtEnergy } from '../utils/dict'

const loading = ref(false)
const data = ref({})
const trendRef = ref()
const deviceRef = ref()
const alarmRef = ref()
const trendChart = useChart(trendRef)
const deviceChart = useChart(deviceRef)
const alarmChart = useChart(alarmRef)

const cards = computed(() => [
  { label: '在运电站 / 总容量', value: `${data.value.station_count || 0} 座 / ${((data.value.total_capacity_kwp || 0) / 1000).toFixed(0)}`, unit: ' MWp', icon: 'OfficeBuilding', color: '#409eff', bg: '#ecf5ff' },
  { label: '今日发电量', value: fmtEnergy(data.value.today_energy), unit: ' kWh', icon: 'Sunny', color: '#e6a23c', bg: '#fdf6ec' },
  { label: '本月累计发电', value: fmtEnergy(data.value.month_energy), unit: ' kWh', icon: 'TrendCharts', color: '#67c23a', bg: '#f0f9eb' },
  { label: '活跃告警', value: data.value.active_alarms || 0, unit: ' 条', icon: 'BellFilled', color: '#f56c6c', bg: '#fef0f0' },
])

const todos = computed(() => [
  { label: '待办巡检工单', value: data.value.pending_inspections || 0, icon: 'DocumentChecked', color: '#409eff', path: '/inspections' },
  { label: '待执行清洗计划', value: data.value.pending_cleanings || 0, icon: 'Brush', color: '#67c23a', path: '/cleanings' },
  { label: '未闭环缺陷', value: data.value.open_defects || 0, icon: 'Tools', color: '#e6a23c', path: '/defects' },
])

onMounted(async () => {
  loading.value = true
  try {
    data.value = await http.get('/overview/')
    renderCharts()
  } finally {
    loading.value = false
  }
})

function renderCharts() {
  const trend = data.value.trend || []
  trendChart.render({
    tooltip: { trigger: 'axis', valueFormatter: (v) => `${Number(v).toLocaleString()} kWh` },
    grid: { left: 60, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: trend.map((t) => t.date), boundaryGap: false },
    yAxis: { type: 'value', name: 'kWh' },
    series: [{
      name: '发电量', type: 'line', smooth: true, data: trend.map((t) => t.energy),
      lineStyle: { width: 3, color: '#409eff' }, showSymbol: false,
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(64,158,255,0.35)' }, { offset: 1, color: 'rgba(64,158,255,0.02)' }],
        },
      },
    }],
  })

  const ds = data.value.device_status || {}
  const devMap = { normal: ['正常', '#67c23a'], warning: ['告警', '#e6a23c'], fault: ['故障', '#f56c6c'], offline: ['离线', '#909399'] }
  deviceChart.render({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
      label: { formatter: '{b}\n{c} 台' },
      data: Object.entries(devMap).map(([k, [label, color]]) => ({
        name: label, value: ds[k] || 0, itemStyle: { color },
      })),
    }],
  })

  const al = data.value.alarm_level || {}
  const lvMap = { info: ['提示', '#909399'], minor: ['一般', '#e6a23c'], major: ['严重', '#f56c6c'], critical: ['紧急', '#c45656'] }
  const keys = Object.keys(lvMap)
  alarmChart.render({
    tooltip: {},
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: keys.map((k) => lvMap[k][0]) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'bar', barWidth: 36,
      data: keys.map((k) => ({ value: al[k] || 0, itemStyle: { color: lvMap[k][1], borderRadius: [4, 4, 0, 0] } })),
    }],
  })
}
</script>

<style scoped>
.stat-inner { display: flex; justify-content: space-between; align-items: center; }
.stat-label { color: #8492a6; font-size: 13px; margin-bottom: 8px; }
.stat-value { font-size: 26px; font-weight: 700; color: #1f2d3d; }
.stat-unit { font-size: 13px; color: #8492a6; font-weight: 400; margin-left: 4px; }
.stat-icon { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.card-title { font-weight: 600; color: #1f2d3d; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.todo-card { cursor: pointer; }
.todo-inner { display: flex; align-items: center; gap: 14px; }
.todo-num { font-size: 24px; font-weight: 700; color: #1f2d3d; }
.todo-label { color: #8492a6; font-size: 13px; }
.todo-arrow { margin-left: auto; color: #c0c4cc; }
</style>
