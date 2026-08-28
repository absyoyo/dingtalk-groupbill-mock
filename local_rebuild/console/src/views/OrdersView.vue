<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fetchBills, fetchBillDetail, openAdminStream } from '../api'
import { ElMessage } from 'element-plus'

const bills = ref([])
const total = ref(0)
const page = ref(1)
const size = 20
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)
const statusFilter = ref('')
const newBillIds = ref(new Set())
let socket = null

const load = async () => {
  const params = { page: page.value, size }
  const body = await fetchBills(params)
  bills.value = body.items || []
  total.value = body.total || 0
}

onMounted(() => {
  load()
  socket = openAdminStream((event) => {
    if (event.type === 'bill.upsert' && event.direction === 'in') {
      const bid = event.payload?.data?.groupBillId
      if (bid) {
        newBillIds.value.add(bid)
        ElMessage.success(`新账单上报: ${bid}`)
      }
      load()
    }
    if (event.type === 'alipay.upload' || event.type === '/api/device/mark_paid') {
      load()
    }
  })
})
onUnmounted(() => socket && socket.close())

const visible = computed(() =>
  statusFilter.value ? bills.value.filter((b) => b.status === statusFilter.value) : bills.value
)

const statusMap = {
  pending: { text: '待拉链接', type: 'info' },
  link_fetched: { text: '已拉链接', type: 'warning' },
  paid: { text: '已付款', type: 'success' },
}

const showDetail = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  detailData.value = await fetchBillDetail(row.groupBillId)
  detailLoading.value = false
}

const newFlag = (bid) => newBillIds.value.has(bid)

const emit = (row) => {
  ElMessage.info(`请到「收款指令」操作此账单: ${row.groupBillId}`)
}

const openCashier = (row) => {
  window.open(`/cashier.html?bill=${encodeURIComponent(row.groupBillId)}`, '_blank')
}
</script>

<template>
  <div>
    <div style="display: flex; gap: 10px; margin-bottom: 8px; align-items: center">
      <el-select v-model="statusFilter" clearable placeholder="状态过滤" style="width: 160px">
        <el-option label="待拉链接" value="pending" />
        <el-option label="已拉链接" value="link_fetched" />
        <el-option label="已付款" value="paid" />
      </el-select>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="visible" height="600">
      <el-table-column label="账单ID" min-width="200">
        <template #default="{ row }">
          <el-badge :hidden="!newFlag(row.groupBillId)" is-dot type="success">
            {{ row.groupBillId }}
          </el-badge>
        </template>
      </el-table-column>
      <el-table-column label="创建者UID" width="140" prop="creatorUid" />
      <el-table-column label="组织ID" width="100" prop="accountId" />
      <el-table-column label="账单条目数" width="110">
        <template #default="{ row }">{{ (row.groupBillItem || []).length }}</template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">{{ new Date(row.timestamp * 1000).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
            {{ statusMap[row.status]?.text || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="emit(row)">拉支付链接</el-button>
          <el-button size="small" type="success" @click="openCashier(row)">付款</el-button>
          <el-button size="small" @click="showDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin-top: 12px"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="size"
      v-model:current-page="page"
      @current-change="load"
    />
    <el-drawer v-model="detailVisible" title="账单聚合详情" direction="rtl" size="60%">
      <div v-loading="detailLoading">
        <pre v-if="detailData" style="white-space: pre-wrap; font-family: monospace; font-size: 12px">{{ JSON.stringify(detailData, null, 2) }}</pre>
      </div>
    </el-drawer>
  </div>
</template>
