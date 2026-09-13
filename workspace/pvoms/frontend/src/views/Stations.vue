<template>
  <div v-loading="loading">
    <el-row :gutter="16">
      <el-col :span="8" v-for="s in stations" :key="s.id" style="margin-bottom: 16px">
        <el-card shadow="hover" class="station-card">
          <div class="card-head">
            <div>
              <div class="station-name">{{ s.name }}</div>
              <div class="station-meta">{{ s.code }} · {{ s.city }}</div>
            </div>
            <el-tag :type="stationStatus[s.status].type">{{ stationStatus[s.status].label }}</el-tag>
          </div>
          <div class="stat-grid">
            <div class="stat-item">
              <div class="num">{{ fmtCapacity(s.capacity_kwp) }}</div>
              <div class="lbl">装机容量</div>
            </div>
            <div class="stat-item">
              <div class="num energy">{{ fmtEnergy(s.today_energy) }}<small> kWh</small></div>
              <div class="lbl">今日发电</div>
            </div>
            <div class="stat-item">
              <div class="num">{{ s.device_count }}</div>
              <div class="lbl">设备数</div>
            </div>
            <div class="stat-item">
              <div class="num" :class="{ warn: s.active_alarms > 0 }">{{ s.active_alarms }}</div>
              <div class="lbl">活跃告警</div>
            </div>
          </div>
          <el-button type="primary" plain style="width: 100%" @click="$router.push(`/stations/${s.id}`)">
            进入电站 →
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import http from '../api'
import { fmtCapacity, fmtEnergy, stationStatus } from '../utils/dict'

const loading = ref(false)
const stations = ref([])

onMounted(async () => {
  loading.value = true
  try {
    stations.value = await http.get('/stations/')
  } catch {
    /* 拦截器已统一提示 */
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.card-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.station-name { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.station-meta { color: #8492a6; font-size: 12px; margin-top: 4px; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.stat-item { background: #f7f9fc; border-radius: 8px; padding: 10px 12px; }
.num { font-size: 18px; font-weight: 700; color: #1f2d3d; }
.num.energy { color: #e6a23c; }
.num.warn { color: #f56c6c; }
.num small { font-size: 12px; font-weight: 400; }
.lbl { font-size: 12px; color: #8492a6; margin-top: 2px; }
</style>
