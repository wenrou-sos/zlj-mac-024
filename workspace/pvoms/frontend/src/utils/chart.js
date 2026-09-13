import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted } from 'vue'

/** ECharts 组合式函数：惰性初始化 + 窗口自适应 */
export function useChart(elRef) {
  let chart = null
  const render = (option) => {
    if (!elRef.value) return
    if (!chart) chart = echarts.init(elRef.value)
    chart.setOption(option)
  }
  const resize = () => chart && chart.resize()
  onMounted(() => window.addEventListener('resize', resize))
  onBeforeUnmount(() => {
    window.removeEventListener('resize', resize)
    chart && chart.dispose()
    chart = null
  })
  return { render }
}
