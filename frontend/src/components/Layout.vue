<template>
  <el-container class="main-layout">
    <el-aside width="200px" class="aside">
      <div class="logo">⚡ 电力运维</div>
      <el-menu
        :default-active="$route.path"
        router
        class="menu"
      >
        <el-menu-item index="/monitor">
          <el-icon><DataBoard /></el-icon>
          <span>监控面板</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI智能对话</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="breadcrumb">{{ $route.meta.title }}</span>
        <div class="header-right">
          <span class="username">管理员</span>
          <el-button type="text" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { DataBoard, ChatDotRound } from '@element-plus/icons-vue'

const router = useRouter()

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100%;
}
.aside {
  background: #001529;
  height: 100vh;
}
.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #2d3a4b;
}
.menu {
  border: none;
  background: transparent;
}
.menu :deep(.el-menu-item) {
  color: #b0b8c4;
}
.menu :deep(.el-menu-item.is-active) {
  color: #fff;
  background: #1890ff !important;
}
.header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.username {
  color: #333;
}
.main-content {
  background: #f0f2f5;
  padding: 24px;
}
</style>