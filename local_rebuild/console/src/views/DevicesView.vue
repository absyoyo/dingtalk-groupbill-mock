<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchDevices, kickDevice, setDeviceRole } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const devices = ref([])
const bindings = ref({})
const load = async () => {
  const body = await fetchDevices()
  devices.value = body.devices || []
  bindings.value = body.bindings || {}
}
let timer = null
onMounted(() => {
  load()
  timer = setInterval(load, 5000)
})
onUnmounted(() => clearInterval(timer))

const kick = async (userId) => {
  const { body } = await kickDevice(userId)
  if (body.code === 0) ElMessage.success(`已踢下线 ${userId}`)
  else ElMessage.error(body.msg || '踢下线失败')
  load()
}

const setRole = async (userId, role) => {
  const { body } = await setDeviceRole(userId, role)
  if (body.code === 0) ElMessage.success(`${userId} 已${role === 'master' ? '绑定为主号' : role === 'slave' ? '绑定为子号' : '解除绑定'}`)
  else ElMessage.error(body.msg || '绑定失败')
  load()
}

const clearRole = async (userId) => {
  try {
    await ElMessageBox.confirm(`确认解除 ${userId} 的角色绑定？`, '提示', { type: 'warning' })
    await setRole(userId, 'clear')
  } catch {}
}

const roleTag = (row) => ({
  type: row.role === 'master' ? 'success' : row.role === 'slave' ? 'warning' : 'info',
  text: row.role === 'master' ? '主号' : row.role === 'slave' ? '子号' : '待识别',
})
</script>

<template>
  <el-table :data="devices">
    <el-table-column prop="userId" label="用户ID" width="140" />
    <el-table-column prop="accountId" label="组织ID" width="100" />
    <el-table-column label="角色" width="120">
      <template #default="{ row }">
        <el-tag :type="roleTag(row).type" size="small">{{ roleTag(row).text }}</el-tag>
        <el-tag v-if="row.roleSource === 'bound'" type="primary" size="small" effect="plain" style="margin-left: 4px">已绑定</el-tag>
        <el-tag v-else size="small" effect="plain" style="margin-left: 4px">自动</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="上线时间" width="180">
      <template #default="{ row }">{{ new Date(row.connectedAt * 1000).toLocaleString() }}</template>
    </el-table-column>
    <el-table-column label="最后心跳" width="100">
      <template #default="{ row }">{{ row.lastPingAt ? new Date(row.lastPingAt * 1000).toLocaleTimeString() : '—' }}</template>
    </el-table-column>
    <el-table-column label="操作" width="320">
      <template #default="{ row }">
        <el-button size="small" type="success" :disabled="row.role === 'master' && row.roleSource === 'bound'" @click="setRole(row.userId, 'master')">设为主号</el-button>
        <el-button size="small" type="warning" :disabled="row.role === 'slave' && row.roleSource === 'bound'" @click="setRole(row.userId, 'slave')">设为子号</el-button>
        <el-button size="small" :disabled="row.roleSource !== 'bound'" @click="clearRole(row.userId)">解绑</el-button>
        <el-button size="small" type="danger" @click="kick(row.userId)">踢下线</el-button>
      </template>
    </el-table-column>
  </el-table>
  <el-card v-if="Object.keys(bindings).length" shadow="never" style="margin-top: 12px">
    <template #header><b>角色绑定记录</b>（持久化到 device-roles.json）</template>
    <el-tag v-for="(role, uid) in bindings" :key="uid" :type="role === 'master' ? 'success' : 'warning'" style="margin: 4px">
      {{ uid }} → {{ role === 'master' ? '主号' : '子号' }}
    </el-tag>
  </el-card>
</template>
