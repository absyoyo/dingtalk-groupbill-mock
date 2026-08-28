<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { openAdminStream } from './api'
import DevicesView from './views/DevicesView.vue'
import SendView from './views/SendView.vue'
import EventsView from './views/EventsView.vue'
import OrdersView from './views/OrdersView.vue'
import LogsView from './views/LogsView.vue'
import ApiDocsView from './views/ApiDocsView.vue'
import GuideView from './views/GuideView.vue'

const active = ref('devices')
const liveCount = ref(0)
const onlineDevices = ref(0)
let socket = null

onMounted(() => {
  socket = openAdminStream((event) => {
    liveCount.value += 1
    if (event.type === 'connected') onlineDevices.value += 1
    if (event.type === 'disconnected' && onlineDevices.value > 0) onlineDevices.value -= 1
  })
})
onUnmounted(() => socket && socket.close())
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside width="200px">
      <el-menu :default-active="active" @select="(key) => (active = key)">
        <el-menu-item index="devices">设备管理</el-menu-item>
        <el-menu-item index="send">收款指令/消息下发</el-menu-item>
        <el-menu-item index="events">事件流</el-menu-item>
        <el-menu-item index="orders">订单查询</el-menu-item>
        <el-menu-item index="logs">日志</el-menu-item>
        <el-menu-item index="guide">操作教程</el-menu-item>
        <el-menu-item index="api">API 文档</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header height="40px" style="display: flex; align-items: center; gap: 16px">
        <span>实时事件: {{ liveCount }}</span>
        <span>在线设备(估): {{ onlineDevices }}</span>
      </el-header>
      <el-main>
        <DevicesView v-if="active === 'devices'" />
        <SendView v-else-if="active === 'send'" />
        <EventsView v-else-if="active === 'events'" />
        <OrdersView v-else-if="active === 'orders'" />
        <LogsView v-else-if="active === 'logs'" />
        <GuideView v-else-if="active === 'guide'" />
        <ApiDocsView v-else-if="active === 'api'" />
        <ApiDocsView v-else />
      </el-main>
    </el-container>
  </el-container>
</template>
