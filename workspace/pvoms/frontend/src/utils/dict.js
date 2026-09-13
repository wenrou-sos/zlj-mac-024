// 业务字典：状态/级别 -> 中文标签与 Element Plus 标签类型
export const stationStatus = {
  running: { label: '运行正常', type: 'success' },
  maintenance: { label: '检修中', type: 'warning' },
  fault: { label: '故障', type: 'danger' },
}

export const deviceStatus = {
  normal: { label: '正常', type: 'success' },
  warning: { label: '告警', type: 'warning' },
  fault: { label: '故障', type: 'danger' },
  offline: { label: '离线', type: 'info' },
}

export const alarmLevel = {
  info: { label: '提示', type: 'info' },
  minor: { label: '一般', type: 'warning' },
  major: { label: '严重', type: 'danger' },
  critical: { label: '紧急', type: 'danger' },
}

export const alarmStatus = {
  open: { label: '未处理', type: 'danger' },
  processing: { label: '处理中', type: 'warning' },
  resolved: { label: '已处理', type: 'success' },
}

export const orderStatus = {
  pending: { label: '待执行', type: 'info' },
  in_progress: { label: '执行中', type: 'warning' },
  done: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'info' },
}

export const orderType = {
  regular: { label: '定期巡检', type: 'primary' },
  special: { label: '专项巡检', type: 'warning' },
  fault: { label: '故障巡检', type: 'danger' },
}

export const cleanStatus = {
  planned: { label: '待执行', type: 'info' },
  in_progress: { label: '进行中', type: 'warning' },
  done: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'info' },
}

export const defectLevel = {
  minor: { label: '一般', type: 'warning' },
  major: { label: '严重', type: 'danger' },
  critical: { label: '危急', type: 'danger' },
}

export const defectStatus = {
  open: { label: '待消缺', type: 'danger' },
  processing: { label: '消缺中', type: 'warning' },
  resolved: { label: '已消缺', type: 'success' },
  cancelled: { label: '已作废', type: 'info' },
}

/** 发电量格式化：>=1万 显示为 万kWh */
export function fmtEnergy(v) {
  if (v == null) return '-'
  return v >= 10000 ? `${(v / 10000).toFixed(2)} 万` : `${Number(v).toFixed(0)}`
}

/** 容量格式化：kWp -> MWp */
export function fmtCapacity(kwp) {
  return `${(kwp / 1000).toFixed(1)} MWp`
}
