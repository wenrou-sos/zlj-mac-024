<template>
  <el-card shadow="never">
    <div class="filter-bar">
      <el-select v-model="filters.station" placeholder="全部电站" clearable style="width: 200px" @change="load">
        <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 130px" @change="load">
        <el-option v-for="(v, k) in orderStatus" :key="k" :label="v.label" :value="k" />
      </el-select>
      <el-button type="primary" :icon="'Plus'" @click="dialog = true">新建工单</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="code" label="工单编号" width="160" />
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="station_name" label="电站" width="160" show-overflow-tooltip />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="orderType[row.order_type].type" size="small" effect="plain">{{ orderType[row.order_type].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assignee" label="执行人" width="90" />
      <el-table-column prop="plan_date" label="计划日期" width="110" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="orderStatus[row.status].type" size="small">{{ orderStatus[row.status].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="result" label="巡检结果" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ row.result || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" type="warning" size="small" link @click="act(row, 'start')">开始执行</el-button>
          <el-button v-if="['pending', 'in_progress'].includes(row.status)" type="success" size="small" link @click="complete(row)">完成</el-button>
          <el-button v-if="['pending', 'in_progress'].includes(row.status)" type="info" size="small" link @click="act(row, 'cancel')">取消</el-button>
          <span v-if="['done', 'cancelled'].includes(row.status)" class="done-text">—</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" title="新建巡检工单" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="电站" required>
          <el-select v-model="form.station" style="width: 100%">
            <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="如：10 月月度巡检" />
        </el-form-item>
        <el-form-item label="巡检类型">
          <el-radio-group v-model="form.order_type">
            <el-radio-button v-for="(v, k) in orderType" :key="k" :value="k">{{ v.label }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="执行人" required>
          <el-input v-model="form.assignee" placeholder="姓名" />
        </el-form-item>
        <el-form-item label="计划日期" required>
          <el-date-picker v-model="form.plan_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
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
import { orderStatus, orderType } from '../utils/dict'

const loading = ref(false)
const rows = ref([])
const stations = ref([])
const dialog = ref(false)
const filters = reactive({ station: null, status: null })
const form = reactive({ station: null, title: '', order_type: 'regular', assignee: '', plan_date: null })

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
    rows.value = await http.get(`/inspections/?${params}`)
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.station || !form.title || !form.assignee || !form.plan_date) {
    ElMessage.warning('请填写完整信息')
    return
  }
  const code = `XJ${form.plan_date.replaceAll('-', '')}-${String(Math.floor(Math.random() * 900) + 100)}`
  await http.post('/inspections/', { ...form, code })
  ElMessage.success('工单已创建')
  dialog.value = false
  Object.assign(form, { station: null, title: '', order_type: 'regular', assignee: '', plan_date: null })
  load()
}

async function act(row, action) {
  await http.post(`/inspections/${row.id}/${action}/`)
  ElMessage.success('操作成功')
  load()
}

async function complete(row) {
  const { value } = await ElMessageBox.prompt('请填写巡检结果', '完成工单', {
    inputValue: '设备运行正常，未发现重大隐患。', inputPattern: /\S+/, inputErrorMessage: '结果不能为空',
  })
  await http.post(`/inspections/${row.id}/complete/`, { result: value })
  ElMessage.success('工单已完成')
  load()
}
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.done-text { color: #909399; }
</style>
