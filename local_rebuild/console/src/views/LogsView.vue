<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchServerLogs, fetchLogcat, toggleLogcat, openAdminStream } from '../api'
import { ElMessage } from 'element-plus'

const tab = ref('logcat')
const serverLogs = ref([])
const logcatLines = ref([])
const serverTotal = ref(0)
const logcatTotal = ref(0)
const keyword = ref('')
const page = ref(1)
const size = 100
const collecting = ref(false)
let socket = null

const loadServer = async () => {
  const data = await fetchServerLogs({ keyword: keyword.value || undefined, page: page.value, size })
  serverLogs.value = data.items
  serverTotal.value = data.total
}

const loadLogcat = async () => {
  const data = await fetchLogcat({ keyword: keyword.value || undefined, page: page.value, size })
  logcatLines.value = data.items
  logcatTotal.value = data.total
}

const load = () => (tab.value === 'logcat' ? loadLogcat() : loadServer())

const onToggle = async () => {
  const { body } = await toggleLogcat()
  if (body.code === 0) {
    collecting.value = body.data.state === 'running'
    ElMessage.success(body.data.state === 'running' ? 'logcat 采集已启动' : 'logcat 采集已停止')
  }
}

onMounted(() => {
  load()
  socket = openAdminStream((event) => {
    if (event.type === 'device.log' && tab.value === 'logcat') {
      logcatLines.value.unshift(JSON.stringify(event.payload))
      if (logcatLines.value.length > 500) logcatLines.value.pop()
    }
  })
})
onUnmounted(() => socket && socket.close())
</script>

<template>
  <div style="display: flex; flex-direction: column; height: 100%; gap: 10px">
    <div style="display: flex; gap: 10px; align-items: center">
      <el-radio-group v-model="tab" @change="load">
        <el-radio-button value="logcat">设备日志 (DtGroupBill)</el-radio-button>
        <el-radio-button value="server">服务器日志</el-radio-button>
      </el-radio-group>
      <el-input v-model="keyword" placeholder="关键字过滤" style="width: 220px" clearable @keyup.enter="load" />
      <el-button @click="load">查询</el-button>
      <el-button :type="collecting ? 'danger' : 'success'" @click="onToggle">
        {{ collecting ? '停止采集' : '启动采集' }}
      </el-button>
    </div>
    <el-input
      v-if="tab === 'logcat'"
      type="textarea"
      :rows="28"
      readonly
      :model-value="logcatLines.join('\n')"
      placeholder="暂无日志 — 点击「启动采集」开始抓取手机 DtGroupBill 日志"
      style="font-family: monospace"
    />
    <el-input
      v-else
      type="textarea"
      :rows="28"
      readonly
      :model-value="serverLogs.join('\n')"
      style="font-family: monospace"
    />
    <el-pagination
      layout="total, prev, pager, next"
      :total="tab === 'logcat' ? logcatTotal : serverTotal"
      :page-size="size"
      v-model:current-page="page"
      @current-change="load"
    />
  </div>
</template>
