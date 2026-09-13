<template>
  <el-card shadow="never">
    <div class="filter-bar">
      <el-select v-model="filters.station" placeholder="全部电站" clearable style="width: 200px" @change="load">
        <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="filters.level" placeholder="全部级别" clearable style="width: 130px" @change="load">
        <el-option v-for="(v, k) in alarmLevel" :key="k" :label="v.label" :value="k" />
      </el-select>
      <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 130px" @change="load">
        <el-option v-for="(v, k) in alarmStatus" :key="k" :label="v.label" :value="k" />
      </el-select>
      <el-button :icon="'Refresh'" circle @click="load" />
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="created_at" label="告警时间" width="150" />
      <el-table-column prop="station_name" label="电站" width="170" show-overflow-tooltip />
      <el-table-column label="级别" width="90">
        <template #default="{ row }">
          <el-tag :type="alarmLevel[row.level].type" size="small">{{ alarmLevel[row.level].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="告警内容" width="220" show-overflow-tooltip />
      <el-table-column prop="message" label="详情" show-overflow-tooltip />
      <el-table-column prop="device_name" label="关联设备" width="120">
        <template #default="{ row }">{{ row.device_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="alarmStatus[row.status].type" size="small" effect="plain">{{ alarmStatus[row.status].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="handler" label="处理人" width="90">
        <template #default="{ row }">{{ row.handler || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'open'" type="warning" size="small" link @click="start(row)">开始处理</el-button>
          <el-button v-if="row.status !== 'resolved'" type="success" size="small" link @click="resolve(row)">标记已处理</el-button>
          <span v-if="row.status === 'resolved'" class="done-text">已闭环</span>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import http from '../api'
import { alarmLevel, alarmStatus } from '../utils/dict'

const loading = ref(false)
const rows = ref([])
const stations = ref([])
const filters = reactive({ station: null, level: null, status: null })

onMounted(async () => {
  try {
    stations.value = await http.get('/stations/')
  } catch {
    /* 拦截器已统一提示 */
  }
  await load()
})

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.station) params.set('station', filters.station)
    if (filters.level) params.set('level', filters.level)
    if (filters.status) params.set('status', filters.status)
    rows.value = await http.get(`/alarms/?${params}`)
  } catch {
    /* 拦截器已统一提示 */
  } finally {
    loading.value = false
  }
}

async function start(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入处理人姓名', '开始处理', {
      inputValue: row.handler || '', inputPattern: /\S+/, inputErrorMessage: '处理人不能为空',
    })
    await http.post(`/alarms/${row.id}/start/`, { handler: value })
    ElMessage.success('已开始处理')
    load()
  } catch {
    /* 用户取消或请求失败（拦截器已提示） */
  }
}

async function resolve(row) {
  try {
    const { value } = await ElMessageBox.prompt('确认告警已处理完成，请输入处理人', '处理完成', {
      inputValue: row.handler || '', inputPattern: /\S+/, inputErrorMessage: '处理人不能为空',
    })
    await http.post(`/alarms/${row.id}/resolve/`, { handler: value })
    ElMessage.success('告警已闭环')
    load()
  } catch {
    /* 用户取消或请求失败（拦截器已提示） */
  }
}
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.done-text { color: #67c23a; font-size: 12px; }
</style>
