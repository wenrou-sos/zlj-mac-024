<template>
  <el-container class="layout">
    <el-aside width="216px" class="sidebar">
      <div class="logo">
        <span class="logo-icon">☀</span> 光伏运维平台
      </div>
      <el-menu :default-active="$route.path" router class="menu"
               background-color="transparent" text-color="#9fb3d1" active-text-color="#ffffff">
        <el-menu-item index="/"><el-icon><Odometer /></el-icon>运行总览</el-menu-item>
        <el-menu-item index="/stations"><el-icon><OfficeBuilding /></el-icon>电站管理</el-menu-item>
        <el-menu-item index="/alarms"><el-icon><BellFilled /></el-icon>异常告警</el-menu-item>
        <el-menu-item index="/inspections"><el-icon><DocumentChecked /></el-icon>巡检工单</el-menu-item>
        <el-menu-item index="/cleanings"><el-icon><Brush /></el-icon>清洗计划</el-menu-item>
        <el-menu-item index="/defects"><el-icon><Tools /></el-icon>消缺记录</el-menu-item>
      </el-menu>
      <div class="sidebar-footer">PVOMS v1.0</div>
    </el-aside>
    <el-container>
      <el-header class="header" height="56px">
        <div class="page-title">{{ $route.meta.title || '运行总览' }}</div>
        <div class="header-right">
          <el-tag type="success" effect="plain" round>● 数据采集中</el-tag>
          <span class="date-text">{{ today }}</span>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.layout { height: 100vh; }
.sidebar {
  background: linear-gradient(180deg, #0d2240 0%, #10315c 100%);
  display: flex; flex-direction: column;
}
.logo {
  color: #fff; font-size: 18px; font-weight: 600; padding: 20px 16px;
  letter-spacing: 1px;
}
.logo-icon { color: #f7c948; margin-right: 4px; }
.menu { border-right: none; flex: 1; }
.menu .el-menu-item { margin: 4px 10px; border-radius: 8px; }
.menu .el-menu-item.is-active { background: rgba(64, 158, 255, 0.35); }
.menu .el-menu-item:hover { background: rgba(255, 255, 255, 0.08); }
.sidebar-footer { color: #5f7ba6; font-size: 12px; text-align: center; padding: 14px; }
.header {
  background: #fff; display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid #e8ecf1; padding: 0 24px;
}
.page-title { font-size: 17px; font-weight: 600; color: #1f2d3d; }
.header-right { display: flex; align-items: center; gap: 14px; }
.date-text { color: #8492a6; font-size: 13px; }
.main { background: #f2f5f9; padding: 20px; overflow-y: auto; }
.stat-card { border-radius: 10px; }
.chart-box { height: 320px; }
</style>
