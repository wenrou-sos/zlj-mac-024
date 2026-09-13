<template>
  <el-card shadow="never">
    <div class="filter-bar">
      <el-select v-model="filters.station" placeholder="全部电站" clearable style="width: 200px" @change="load">
        <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 130px" @change="load">
        <el-option v-for="(v, k) in cleanStatus" :key="k" :label="v.label" :value="k" />
      </el-select>
      <el-button type="primary" :icon="'Plus'" @click="dialog = true">新建清洗计划</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="code" label="计划编号" width="160" />
      <el-table-column prop="station_name" label="电站" width="180" show-overflow-tooltip />
      <el-table-column prop="area" label="清洗区域" min-width="150" />
      <el-table-column prop="plan_date" label="计划日期" width="110" />
      <el-table-column prop="executor" label="执行班组" width="120" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="cleanStatus[row.status].type" size="small">{{ cleanStatus[row.status].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="finished_at" label="完成时间" width="140">
        <template #default="{ row }">{{ row.finished_at || '-' }}</template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ row.note || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'planned'" type="warning" size="small" link @click="act(row, 'start')">开始</el-button>
          <el-button v-if="['planned', 'in_progress'].includes(row.status)" type="success" size="small" link @click="complete(row)">完成</el-button>
          <el-button v-if="['planned', 'in_progress'].includes(row.status)" type="info" size="small" link @click="act(row, 'cancel')">取消</el-button>
          <span v-if="['done', 'cancelled'].includes(row.status)" class="done-text">—</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" title="新建清洗计划" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="电站" required>
          <el-select v-model="form.station" style="width: 100%">
            <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="清洗区域" required>
          <el-input v-model="form.area" placeholder="如：一期 A 区方阵" />
        </el-form-item>
        <el-form-item label="计划日期" required>
          <el-date-picker v-model="form.plan_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="执行班组" required>
          <el-input v-model="form.executor" placeholder="如：清洗一班 / 外委清洗队" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="create">创建</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import http from '../api'
import { cleanStatus } from '../utils/dict'

const loading = ref(false)
const rows = ref([])
const stations = ref([])
const dialog = ref(false)
const filters = reactive({ station: null, status: null })
const form = reactive({ station: null, area: '', plan_date: null, executor: '', note: '' })

onMounted(async () => {
  stations.value = await http.get('/stations/')
  await load()
})

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.station) params.set('station', filters.station)
    if (filters.status) params.set('status', filters.status)
    rows.value = await http.get(`/cleanings/?${params}`)
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.station || !form.area || !form.plan_date || !form.executor) {
    ElMessage.warning('请填写完整信息')
    return
  }
  const code = `QX${form.plan_date.replaceAll('-', '')}-${String(Math.floor(Math.random() * 900) + 100)}`
  await http.post('/cleanings/', { ...form, code })
  ElMessage.success('清洗计划已创建')
  dialog.value = false
  Object.assign(form, { station: null, area: '', plan_date: null, executor: '', note: '' })
  load()
}

async function act(row, action) {
  await http.post(`/cleanings/${row.id}/${action}/`)
  ElMessage.success('操作成功')
  load()
}

async function complete(row) {
  const { value } = await ElMessageBox.prompt('请填写清洗完成情况备注', '完成清洗', {
    inputValue: '清洗完成，组件表面清洁度良好。', inputPattern: /\S+/, inputErrorMessage: '备注不能为空',
  })
  await http.post(`/cleanings/${row.id}/complete/`, { note: value })
  ElMessage.success('清洗计划已完成')
  load()
}
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.done-text { color: #909399; }
</style>
