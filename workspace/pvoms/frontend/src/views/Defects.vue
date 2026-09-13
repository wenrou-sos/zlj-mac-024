<template>
  <el-card shadow="never">
    <div class="filter-bar">
      <el-select v-model="filters.station" placeholder="全部电站" clearable style="width: 200px" @change="load">
        <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="filters.level" placeholder="全部级别" clearable style="width: 130px" @change="load">
        <el-option v-for="(v, k) in defectLevel" :key="k" :label="v.label" :value="k" />
      </el-select>
      <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 130px" @change="load">
        <el-option v-for="(v, k) in defectStatus" :key="k" :label="v.label" :value="k" />
      </el-select>
      <el-button type="primary" :icon="'Plus'" @click="openDialog">登记缺陷</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="code" label="缺陷编号" width="160" />
      <el-table-column prop="station_name" label="电站" width="160" show-overflow-tooltip />
      <el-table-column prop="description" label="缺陷描述" min-width="220" show-overflow-tooltip />
      <el-table-column prop="device_name" label="关联设备" width="120">
        <template #default="{ row }">{{ row.device_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="级别" width="80">
        <template #default="{ row }">
          <el-tag :type="defectLevel[row.level].type" size="small">{{ defectLevel[row.level].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="defectStatus[row.status].type" size="small" effect="plain">{{ defectStatus[row.status].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reporter" label="发现人" width="90" />
      <el-table-column prop="found_at" label="发现日期" width="105" />
      <el-table-column prop="handler" label="消缺人" width="90">
        <template #default="{ row }">{{ row.handler || '-' }}</template>
      </el-table-column>
      <el-table-column prop="solution" label="处理措施" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ row.solution || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'open'" type="warning" size="small" link @click="start(row)">开始消缺</el-button>
          <el-button v-if="row.status !== 'resolved'" type="success" size="small" link @click="resolve(row)">完成消缺</el-button>
          <span v-if="row.status === 'resolved'" class="done-text">已闭环</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" title="登记缺陷" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="电站" required>
          <el-select v-model="form.station" style="width: 100%" @change="loadDevices">
            <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联设备">
          <el-select v-model="form.device" clearable placeholder="可不选" style="width: 100%">
            <el-option v-for="d in devices" :key="d.id" :label="`${d.name}（${d.type_display}）`" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="缺陷级别">
          <el-radio-group v-model="form.level">
            <el-radio-button v-for="(v, k) in defectLevel" :key="k" :value="k">{{ v.label }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="缺陷描述" required>
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="缺陷现象、位置、影响范围" />
        </el-form-item>
        <el-form-item label="发现人" required>
          <el-input v-model="form.reporter" />
        </el-form-item>
        <el-form-item label="发现日期" required>
          <el-date-picker v-model="form.found_at" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="create">登记</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import http from '../api'
import { defectLevel, defectStatus } from '../utils/dict'

const loading = ref(false)
const rows = ref([])
const stations = ref([])
const devices = ref([])
const dialog = ref(false)
const filters = reactive({ station: null, level: null, status: null })
const form = reactive({ station: null, device: null, level: 'minor', description: '', reporter: '', found_at: null })

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
    rows.value = await http.get(`/defects/?${params}`)
  } catch {
    /* 拦截器已统一提示 */
  } finally {
    loading.value = false
  }
}

function openDialog() {
  form.found_at = new Date().toISOString().slice(0, 10)
  dialog.value = true
}

async function loadDevices(stationId) {
  form.device = null
  try {
    devices.value = stationId ? await http.get(`/devices/?station=${stationId}`) : []
  } catch {
    devices.value = []
  }
}

async function create() {
  if (!form.station || !form.description || !form.reporter || !form.found_at) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    const code = `XQ${form.found_at.replaceAll('-', '')}-${String(Date.now()).slice(-6)}`
    await http.post('/defects/', { ...form, code })
    ElMessage.success('缺陷已登记')
    dialog.value = false
    Object.assign(form, { station: null, device: null, level: 'minor', description: '', reporter: '', found_at: null })
    load()
  } catch {
    /* 拦截器已统一提示 */
  }
}

async function start(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入消缺负责人', '开始消缺', {
      inputValue: row.handler || '', inputPattern: /\S+/, inputErrorMessage: '负责人不能为空',
    })
    await http.post(`/defects/${row.id}/start/`, { handler: value })
    ElMessage.success('已开始消缺')
    load()
  } catch {
    /* 用户取消或请求失败（拦截器已提示） */
  }
}

async function resolve(row) {
  try {
    const { value } = await ElMessageBox.prompt('请填写处理措施', '完成消缺', {
      inputValue: '已处理完毕，设备恢复正常运行。', inputPattern: /\S+/, inputErrorMessage: '处理措施不能为空',
    })
    await http.post(`/defects/${row.id}/resolve/`, { solution: value, handler: row.handler || '运维班' })
    ElMessage.success('缺陷已闭环')
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
