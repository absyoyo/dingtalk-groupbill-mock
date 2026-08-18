<script setup>
import { ref } from 'vue'

const groups = [
  {
    name: '基础',
    color: 'info',
    apis: [
      { method: 'GET', path: '/health', summary: '健康检查', desc: '服务器存活探针' },
    ],
  },
  {
    name: '设备上报',
    color: 'success',
    apis: [
      { method: 'POST', path: '/api/device/upload_order', summary: '上报订单', desc: 'APK 发起群收款时上报 user/pay_order/pay_id/amount' },
      { method: 'POST', path: '/api/device/upload_sdk', summary: '上报SDK参数', desc: 'APK 调起支付SDK时上报 pay_id/sdk_param' },
      { method: 'POST', path: '/api/device/mark_paid', summary: '标记已支付', desc: 'APK 支付成功后上报 pay_id' },
    ],
  },
  {
    name: '设备管理',
    color: 'warning',
    apis: [
      { method: 'GET', path: '/api/admin/devices', summary: '设备列表+角色', desc: '返回所有在线设备，含 role（master/slave/unknown）和 roleSource（bound/auto）' },
      { method: 'POST', path: '/api/admin/devices/{userId}/role', summary: '绑定角色', desc: '把 userId 绑定为主号/子号，持久化到 device-roles.json。Body: {role:"master"|"slave"|"clear"}' },
      { method: 'DELETE', path: '/api/admin/devices/{userId}', summary: '踢下线', desc: '断开 userId 的 WebSocket 连接' },
    ],
  },
  {
    name: '账单中心',
    color: 'primary',
    apis: [
      { method: 'GET', path: '/api/admin/bills', summary: '账单列表', desc: '从 bill.upsert 提取所有账单，含状态聚合（pending/link_fetched/paid）' },
      { method: 'GET', path: '/api/admin/bills/{groupBillId}', summary: '账单聚合详情', desc: '返回单笔账单的所有关联事件' },
    ],
  },
  {
    name: '收款指令',
    color: 'danger',
    apis: [
      { method: 'POST', path: '/api/admin/collect', summary: '拉支付链接', desc: '下发 bill.task 给子号，等待 alipay.upload 回调返回 payUrl。Body: {groupBillId, targetUid, creatorUid?, timeoutSeconds}' },
      { method: 'POST', path: '/api/admin/query-detail', summary: '查账单详情', desc: '下发 rpc.call detail，等待 rpc.result' },
      { method: 'POST', path: '/api/admin/query-pay-status', summary: '查支付状态', desc: '下发 rpc.call probePayStatus，等待 rpc.result' },
      { method: 'POST', path: '/api/admin/send', summary: '通用消息下发', desc: '下发 allowlist 消息到指定 userId 或广播，不等回调' },
    ],
  },
  {
    name: '事件流',
    color: 'info',
    apis: [
      { method: 'GET', path: '/api/admin/events', summary: '事件历史', desc: '分页查询所有事件，支持 type/transport/direction 过滤' },
      { method: 'GET', path: '/api/admin/orders', summary: '订单上报记录', desc: '分页查询 upload_order HTTP 上报记录' },
    ],
  },
  {
    name: '日志',
    color: 'success',
    apis: [
      { method: 'GET', path: '/api/admin/logs', summary: '服务器日志', desc: '分页查询 uvicorn stdout，支持 level/keyword 过滤' },
      { method: 'GET', path: '/api/admin/logcat', summary: '设备logcat', desc: '分页查询手机 DtGroupBill logcat' },
      { method: 'POST', path: '/api/admin/logcat/toggle', summary: '启停logcat采集', desc: '启动/停止 adb logcat 后台采集' },
    ],
  },
  {
    name: 'WebSocket',
    color: 'warning',
    apis: [
      { method: 'WS', path: '/ws', summary: 'APK实时通信', desc: 'APK 端连接，收发 register/ping/bill.upsert/alipay.upload 等消息' },
      { method: 'WS', path: '/api/admin/ws', summary: '控制台事件流', desc: '订阅实时事件流（所有 in/out 事件）' },
    ],
  },
]

const methodColor = { GET: 'success', POST: 'warning', DELETE: 'danger', WS: 'primary' }
const curlExample = `curl -X POST http://192.168.3.4:18722/api/admin/collect \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: your-key" \\
  -d '{"groupBillId":"bill-001","targetUid":"199504987","timeoutSeconds":30}'`
</script>

<template>
  <div>
    <el-alert type="info" :closable="false" style="margin-bottom: 16px">
      <template #title>
        <b>API 开放能力</b> — 所有接口统一返回 <code>{"code":0,"msg":"成功","data":...}</code> 格式
      </template>
      <div style="display: flex; gap: 16px; margin-top: 8px; flex-wrap: wrap">
        <el-link type="primary" href="/docs" target="_blank">Swagger 文档（在线试调）</el-link>
        <el-link type="primary" href="/redoc" target="_blank">ReDoc 文档</el-link>
        <el-link type="primary" href="/openapi.json" target="_blank">OpenAPI JSON</el-link>
      </div>
    </el-alert>

    <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
      <template #title>API Key 鉴权</template>
      若设置了环境变量 <code>API_KEY</code>，所有 <code>/api/admin/*</code> 接口需在请求头携带 <code>X-API-Key: your-key</code>。未设置时为开放模式（无需鉴权）。
    </el-alert>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>调用示例</b>（拉支付链接）</template>
      <pre style="background: #f5f7fa; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 12px; overflow-x: auto">{{ curlExample }}</pre>
    </el-card>

    <el-collapse v-for="g in groups" :key="g.name" v-model="g.open" style="margin-bottom: 8px">
      <el-collapse-item :title="g.name" :name="g.name" default-open>
        <el-table :data="g.apis" size="small" border>
          <el-table-column label="方法" width="80">
            <template #default="{ row }">
              <el-tag :type="methodColor[row.method]" size="small">{{ row.method }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="路径" width="280">
            <template #default="{ row }"><code>{{ row.path }}</code></template>
          </el-table-column>
          <el-table-column prop="summary" label="功能" width="160" />
          <el-table-column prop="desc" label="说明" />
        </el-table>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>
