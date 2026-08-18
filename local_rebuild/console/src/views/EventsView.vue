<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { openAdminStream } from '../api'
import { ElMessage } from 'element-plus'

const events = ref([])
const paused = ref(false)
const typeFilter = ref('')
const directionFilter = ref('')
const eventTypes = [
  { value: 'bill.upsert', label: '账单上报（主号发起群收款）' },
  { value: 'bill.task', label: '收款指令下发' },
  { value: 'alipay.upload', label: '支付链接上报（含 payUrl）' },
  { value: 'rpc.call', label: '远程RPC调用下发' },
  { value: 'rpc.result', label: 'RPC结果上报' },
  { value: '/api/device/upload_order', label: '订单HTTP上报' },
  { value: '/api/device/upload_sdk', label: 'SDK参数HTTP上报' },
  { value: '/api/device/mark_paid', label: '已支付HTTP上报' },
  { value: 'register', label: '设备注册' },
  { value: 'ack', label: '注册确认' },
  { value: 'ping', label: '心跳' },
  { value: 'connected', label: 'WS连接建立' },
  { value: 'disconnected', label: 'WS连接断开' },
]
let socket = null
let pending = []

onMounted(() => {
  socket = openAdminStream((event) => {
    if (paused.value) {
      pending.push(event)
      return
    }
    events.value.push(event)
    if (events.value.length > 300) events.value.splice(0, events.value.length - 300)
  })
})
onUnmounted(() => socket && socket.close())

const resume = () => {
  paused.value = false
  events.value.push(...pending)
  pending = []
}

const visible = computed(() =>
  events.value.filter(
    (e) =>
      (!typeFilter.value || e.type.includes(typeFilter.value)) &&
      (!directionFilter.value || e.direction === directionFilter.value)
  )
)

const rowClass = ({ row }) => (row.type === 'alipay.upload' ? 'pay-row' : '')

const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; margin-bottom: 8px">
      <el-select v-model="typeFilter" clearable filterable placeholder="类型过滤" style="width: 280px">
        <el-option v-for="t in eventTypes" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <el-select v-model="directionFilter" clearable placeholder="方向" style="width: 120px">
        <el-option label="in" value="in" />
        <el-option label="out" value="out" />
      </el-select>
      <el-button v-if="!paused" @click="paused = true">暂停</el-button>
      <el-button v-else type="primary" @click="resume">继续</el-button>
    </div>
    <el-table :data="visible" height="600" :row-class-name="rowClass">
      <el-table-column label="时间" width="180">
        <template #default="{ row }">{{ new Date(row.timestamp * 1000).toLocaleTimeString() }}</template>
      </el-table-column>
      <el-table-column prop="transport" label="通道" width="80" />
      <el-table-column prop="direction" label="方向" width="70" />
      <el-table-column prop="type" label="类型" width="220" />
      <el-table-column label="内容">
        <template #default="{ row }">
          <template v-if="row.type === 'alipay.upload' && row.payload?.data?.payUrl">
            <el-tag type="success" size="small">支付链接</el-tag>
            <div style="font-family: monospace; font-size: 12px; word-break: break-all; margin-top: 4px">
              {{ row.payload.data.payUrl.slice(0, 300) }}{{ row.payload.data.payUrl.length > 300 ? '…' : '' }}
            </div>
            <div style="margin-top: 4px">
              <el-button size="small" text type="primary" @click="copyText(row.payload.data.payUrl)">复制完整链接</el-button>
            </div>
          </template>
          <template v-else>{{ JSON.stringify(row.payload).slice(0, 160) }}</template>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style>
.pay-row { background: #f0f9eb; }
</style>