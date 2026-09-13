<template>
  <div v-loading="loading">
    <el-card shadow="never" v-if="station">
      <div class="head">
        <div>
          <div class="name">
            {{ station.name }}
            <el-tag :type="stationStatus[station.status].type" style="margin-left: 8px">
              {{ stationStatus[station.status].label }}
            </el-tag>
          </div>
          <div class="meta">{{ station.code }} · {{ station.city }} · {{ station.owner }}</div>
        </div>
        <el-button @click="$router.back()">← 返回</el-button>
      </div>
      <el-descriptions :column="4" border size="small" style="margin-top: 12px">
        <el-descriptions-item label="装机容量">{{ fmtCapacity(station.capacity_kwp) }}</el-descriptions-item>
        <el-descriptions-item label="今日发电">{{ fmtEnergy(station.today_energy) }} kWh</el-descriptions-item>
        <el-descriptions-item label="并网日期">{{ station.grid_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ station.contact || '-' }}</el-descriptions-item>
        <el-descriptions-item label="简介" :span="4">{{ station.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="chart-head">
          <span class="card-title">发电数据</span>
          <el-radio-group v-model="mode" size="small" @change="loadPower">
            <el-radio-button value="30">近 30 天</el-radio-button>
            <el-radio-button value="90">近 90 天</el-radio-button>
            <el-radio-button value="hourly">今日逐时</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="powerRef" class="chart-box"></div>
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header><span class="card-title">设备清单（{{ devices.length }} 台）</span></template>
          <el-table :data="devices" size="small" max-height="360">
            <el-table-column prop="name" label="设备名称" width="130" />
            <el-table-column prop="type_display" label="类型" width="110" />
            <el-table-column prop="model" label="型号" show-overflow-tooltip />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="deviceStatus[row.status].type" size="small">{{ deviceStatus[row.status].label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="install_date" label="安装日期" width="100" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span class="card-title">本站告警</span></template>
          <el-table :data="alarms" size="small" max-height="360">
            <el-table-column prop="created_at" label="时间" width="130" />
            <el-table-column label="级别" width="70">
              <template #default="{ row }">
                <el-tag :type="alarmLevel[row.level].type" size="small">{{ alarmLevel[row.level].label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="内容" show-overflow-tooltip />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="alarmStatus[row.status].type" size="small" effect="plain">{{ alarmStatus[row.status].label }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import http from '../api'
import { useChart } from '../utils/chart'
import { alarmLevel, alarmStatus, deviceStatus, fmtCapacity, fmtEnergy, stationStatus } from '../utils/dict'

const route = useRoute()
const id = route.params.id
const loading = ref(false)
const station = ref(null)
const devices = ref([])
const alarms = ref([])
const mode = ref('30')
const powerRef = ref()
const powerChart = useChart(powerRef)

onMounted(async () => {
  loading.value = true
  try {
    const [s, d, a] = await Promise.all([
      http.get(`/stations/${id}/`),
      http.get(`/stations/${id}/devices/`),
      http.get(`/alarms/?station=${id}`),
    ])
    station.value = s
    devices.value = d
    alarms.value = a
    await loadPower()
  } finally {
    loading.value = false
  }
})

async function loadPower() {
  if (mode.value === 'hourly') {
    const data = await http.get(`/stations/${id}/power_hourly/`)
    powerChart.render({
      tooltip: { trigger: 'axis', valueFormatter: (v) => `${v} kW` },
      grid: { left: 60, right: 20, top: 30, bottom: 30 },
      xAxis: { type: 'category', data: data.map((d) => d.hour), boundaryGap: false },
      yAxis: { type: 'value', name: 'kW' },
      series: [{
        name: '出力功率', type: 'line', smooth: true, showSymbol: false,
        data: data.map((d) => d.power_kw), lineStyle: { color: '#e6a23c', width: 3 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(230,162,60,0.4)' }, { offset: 1, color: 'rgba(230,162,60,0.02)' }],
          },
        },
      }],
    })
  } else {
    const data = await http.get(`/stations/${id}/power/?days=${mode.value}`)
    powerChart.render({
      tooltip: { trigger: 'axis' },
      legend: { top: 0 },
      grid: { left: 70, right: 60, top: 40, bottom: 30 },
      xAxis: { type: 'category', data: data.map((d) => d.date.slice(5)) },
      yAxis: [
        { type: 'value', name: '发电量(kWh)' },
        { type: 'value', name: 'PR(%)', min: 60, max: 100 },
      ],
      series: [
        { name: '日发电量', type: 'bar', barMaxWidth: 18, data: data.map((d) => d.energy_kwh), itemStyle: { color: '#409eff', borderRadius: [3, 3, 0, 0] } },
        { name: '系统效率PR', type: 'line', yAxisIndex: 1, smooth: true, showSymbol: false, data: data.map((d) => d.pr), lineStyle: { color: '#67c23a' } },
      ],
    })
  }
}
</script>

<style scoped>
.head { display: flex; justify-content: space-between; align-items: flex-start; }
.name { font-size: 20px; font-weight: 700; color: #1f2d3d; }
.meta { color: #8492a6; font-size: 13px; margin-top: 6px; }
.card-title { font-weight: 600; color: #1f2d3d; }
.chart-head { display: flex; justify-content: space-between; align-items: center; }
</style>
