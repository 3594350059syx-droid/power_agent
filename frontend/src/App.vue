<template>
  <el-container style="height: 100vh;">
    <el-aside width="200px" style="background-color: rgb(238, 241, 246);">
      <el-menu router default-active="/chat">
        <el-menu-item index="/chat">AI对话诊断</el-menu-item>
        <el-menu-item index="/monitor">实时监控面板</el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
}
</style>