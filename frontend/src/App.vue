<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="logo">📈 A股智能交易评分系统</div>
      <el-menu mode="horizontal" router :default-active="$route.path" class="nav-menu">
        <el-menu-item index="/chart/000001">K线分析面板</el-menu-item>
        <el-menu-item index="/pool">股票池管理</el-menu-item>
        <el-menu-item index="/console">分析调度控制台</el-menu-item>
      </el-menu>
    </el-header>

    <el-main>
      <router-view v-slot="{ Component, route }">
        <component :is="Component" :key="route.fullPath" />
      </router-view>
    </el-main>
  </el-container>
</template>

<style>
body { margin: 0; font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif; background-color: #f5f7fa; }
.app-container { min-height: 100vh; }
.app-header { display: flex; align-items: center; background-color: #fff; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05); z-index: 100; padding: 0 20px; }
.logo { font-size: 20px; font-weight: bold; color: #409EFF; margin-right: 40px; }
.nav-menu { flex: 1; border-bottom: none !important; }
</style>