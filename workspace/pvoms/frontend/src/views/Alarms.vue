<template>
  <el-card shadow="never">
    <el-alert v-if="filters.alarm_id" type="info" class="filter-banner" show-icon
              :title="`正在查看告警 #${filters.alarm_id}（来自派单跳转）`"
              @close="clearAlarmFilter" />
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
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-box">
            <p><b>告警详情：</b>{{ row.message || '—' }}</p>
            <p><b>处置措施：</b>{{ row.handle_note || '—' }}</p>
            <p><b>处理时间：</b>{{ row.handled_at || '—' }}</p>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="告警时间" width="150" />
      <el-table-column prop="station_name" label="电站" width="160" show-overflow-tooltip />
      <el-table-column label="级别" width="80">
        <template #default="{ row }">
          <el-tag :type="alarmLevel[row.level].type" size="small">{{ alarmLevel[row.level].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="告警内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="device_name" label="关联设备" width="110">
        <template #default="{ row }">{{ row.device_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="85">
        <template #default="{ row }">
          <el-tag :type="alarmStatus[row.status].type" size="small" effect="plain">{{ alarmStatus[row.status].label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="派单状态" width="215">
        <template #default="{ row }">
          <el-link v-if="row.dispatch_info" type="primary" class="dispatch-link"
                   @click="goOrder(row)">
            已派单 {{ row.dispatch_info.code }}（{{ row.dispatch_info.status_display }}）
          </el-link>
          <span v-else class="no-dispatch">未派单</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="210" fixed="right">
        <template #default="{ row }">
          <el-button v-if="canDispatch(row)" type="primary" size="small" link @click="openDispatch(row)">派单</el-button>
          <el-button v-if="row.status === 'open'" type="warning" size="small" link @click="start(row)">开始处理</el-button>
          <el-button v-if="row.status !== 'resolved'" type="success" size="small" link @click="openResolve(row)">闭环</el-button>
          <span v-if="row.status === 'resolved'" class="done-text">已闭环</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 派单对话框 -->
    <el-dialog v-model="dispatchDialog" title="告警派单" width="540px">
      <template v-if="dispatchRow">
        <el-descriptions :column="1" border size="small" class="dispatch-desc">
          <el-descriptions-item label="电站">{{ dispatchRow.station_name }}</el-descriptions-item>
          <el-descriptions-item label="关联设备">{{ dispatchRow.device_name || '未关联设备' }}</el-descriptions-item>
          <el-descriptions-item label="告警内容">
            【{{ alarmLevel[dispatchRow.level].label }}】{{ dispatchRow.title }}
            <div class="dispatch-msg">{{ dispatchRow.message }}</div>
          </el-descriptions-item>
        </el-descriptions>
        <el-form label-width="90px">
          <el-form-item label="派单类型">
            <el-radio-group v-model="dispatchForm.type">
              <el-radio-button value="defect">生成消缺记录</el-radio-button>
              <el-radio-button value="inspection">生成巡检工单</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <template v-if="dispatchForm.type === 'defect'">
            <el-form-item label="缺陷级别">
              <el-radio-group v-model="dispatchForm.level">
                <el-radio-button v-for="(v, k) in defectLevel" :key="k" :value="k">{{ v.label }}</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="发现人">
              <el-input v-model="dispatchForm.reporter" placeholder="默认为告警处理人或值班员" />
            </el-form-item>
          </template>
          <template v-else>
            <el-form-item label="执行人" required>
              <el-input v-model="dispatchForm.assignee" placeholder="巡检执行人姓名" />
            </el-form-item>
            <el-form-item label="计划日期">
              <el-date-picker v-model="dispatchForm.plan_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </template>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="dispatchDialog = false">取消</el-button>
        <el-button type="primary" @click="doDispatch">确认派单</el-button>
      </template>
    </el-dialog>

    <!-- 闭环对话框 -->
    <el-dialog v-model="resolveDialog" title="告警闭环" width="460px">
      <el-form label-width="90px">
        <el-form-item label="处理人" required>
          <el-input v-model="resolveForm.handler" />
        </el-form-item>
        <el-form-item label="处置措施">
          <el-input v-model="resolveForm.note" type="textarea" :rows="3"
                    placeholder="可补记处置措施，留下处理痕迹（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resolveDialog = false">取消</el-button>
        <el-button type="success" @click="doResolve">确认闭环</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api'
import { alarmLevel, alarmStatus, defectLevel } from '../utils/dict'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const rows = ref([])
const stations = ref([])
const filters = reactive({ station: null, level: null, status: null, alarm_id: null })

const dispatchDialog = ref(false)
const dispatchRow = ref(null)
const dispatchForm = reactive({ type: 'defect', level: 'minor', reporter: '', assignee: '', plan_date: '' })

const resolveDialog = ref(false)
const resolveRow = ref(null)
const resolveForm = reactive({ handler: '', note: '' })

onMounted(async () => {
  if (route.query.alarm_id) filters.alarm_id = route.query.alarm_id
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
    if (filters.alarm_id) params.set('alarm_id', filters.alarm_id)
    rows.value = await http.get(`/alarms/?${params}`)
  } catch {
    /* 拦截器已统一提示 */
  } finally {
    loading.value = false
  }
}

function clearAlarmFilter() {
  filters.alarm_id = null
  router.replace({ query: {} })
  load()
}

/** 可派单：未闭环 且 没有有效（未取消）派单 */
function canDispatch(row) {
  if (row.status === 'resolved') return false
  const d = row.dispatch_info
  return !d || d.status === 'cancelled'
}

function goOrder(row) {
  const d = row.dispatch_info
  if (!d) return
  const path = d.type === 'defect' ? '/defects' : '/inspections'
  router.push(`${path}?alarm=${row.id}`)
}

function openDispatch(row) {
  dispatchRow.value = row
  const levelMap = { info: 'minor', minor: 'minor', major: 'major', critical: 'critical' }
  Object.assign(dispatchForm, {
    type: 'defect',
    level: levelMap[row.level] || 'minor',
    reporter: row.handler || '',
    assignee: '',
    plan_date: new Date().toISOString().slice(0, 10),
  })
  dispatchDialog.value = true
}

async function doDispatch() {
  const payload = { type: dispatchForm.type }
  if (dispatchForm.type === 'defect') {
    payload.level = dispatchForm.level
    payload.reporter = dispatchForm.reporter
  } else {
    if (!dispatchForm.assignee.trim()) {
      ElMessage.warning('请填写巡检执行人')
      return
    }
    payload.assignee = dispatchForm.assignee.trim()
    payload.plan_date = dispatchForm.plan_date
  }
  try {
    const resp = await http.post(`/alarms/${dispatchRow.value.id}/dispatch/`, payload)
    const label = dispatchForm.type === 'defect' ? '消缺记录' : '巡检工单'
    ElMessage.success(`已生成${label} ${resp.order.code}`)
    dispatchDialog.value = false
    load()
  } catch {
    /* 拦截器已提示明确原因（重复派单/已闭环等） */
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

function openResolve(row) {
  resolveRow.value = row
  resolveForm.handler = row.handler || ''
  resolveForm.note = ''
  resolveDialog.value = true
}

async function doResolve() {
  if (!resolveForm.handler.trim()) {
    ElMessage.warning('请填写处理人')
    return
  }
  try {
    await http.post(`/alarms/${resolveRow.value.id}/resolve/`, {
      handler: resolveForm.handler.trim(),
      note: resolveForm.note.trim(),
    })
    ElMessage.success('告警已闭环')
    resolveDialog.value = false
    load()
  } catch {
    /* 拦截器已统一提示 */
  }
}
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.filter-banner { margin-bottom: 14px; }
.done-text { color: #67c23a; font-size: 12px; }
.no-dispatch { color: #c0c4cc; font-size: 12px; }
.dispatch-link { font-size: 12px; }
.dispatch-desc { margin-bottom: 16px; }
.dispatch-msg { color: #8492a6; font-size: 12px; margin-top: 4px; }
.expand-box { padding: 4px 24px; color: #5e6d82; font-size: 13px; line-height: 1.9; }
</style>
