<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import { fetchBillDetail, queryPayStatus } from './api'

// 群收款账单的 payUrl 是支付宝 App 支付 orderStr（method=alipay.fund.trans.app.pay，
// RSA2 签名的完整订单串）。官方用途即"返回给客户端唤起收银台"；在网页环境通过
// 支付宝客户端收银台组件（appId=20000125）+ orderSuffix 拉起：
//   alipays://platformapi/startapp?appId=20000125&orderSuffix=<urlencoded(orderStr)>
function buildAlipayScheme(payUrl) {
  return `alipays://platformapi/startapp?appId=20000125&orderSuffix=${encodeURIComponent(payUrl)}`
}

const isMobile = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent)

const billId = new URLSearchParams(location.search).get('bill') || ''
const loading = ref(true)
const detail = ref(null)
const loadError = ref('')
const paying = ref(false)
const probing = ref(false)
const selectedPayer = ref('')
const qrDataUrl = ref('')
const payLink = ref('')

const model = computed(() => detail.value?.upsert?.groupBillModel || null)
const items = computed(() => {
  const fromModel = model.value?.groupBillItem
  if (Array.isArray(fromModel) && fromModel.length) return fromModel
  return detail.value?.upsert?.groupBillItem || []
})

// 每个付款人最新的 alipay.upload payUrl（同一 payId 会因重试产生多条，取最新）
function latestPayUrlByPayer() {
  const latest = new Map()
  for (const event of detail.value?.events || []) {
    if (event.type !== 'alipay.upload') continue
    const data = event.payload?.data || {}
    if (!data.payUrl || !data.payerUid) continue
    const prev = latest.get(data.payerUid)
    if (!prev || event.timestamp > prev.timestamp) {
      latest.set(data.payerUid, { timestamp: event.timestamp, payUrl: data.payUrl })
    }
  }
  return latest
}

const payerRows = computed(() => {
  const latest = latestPayUrlByPayer()
  return items.value.map((item) => ({
    uid: String(item.uid),
    amount: item.amount,
    payStatus: item.payStatus,
    // 真实钉钉语义（实测取证）：创建账单时所有条目 payStatus=1 且无人支付，
    // 即 1=待支付；已支付为 2（尚未观测到真实样本，按枚举惯例处理）
    paid: String(item.payStatus) === '2',
    hasPayUrl: latest.has(String(item.uid)),
  }))
})

const selectedRow = computed(() => payerRows.value.find((r) => r.uid === selectedPayer.value) || null)
const paidCount = computed(() => payerRows.value.filter((r) => r.paid).length)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    // fetchBillDetail 返回 body.data（数据本身）或 null
    const data = await fetchBillDetail(billId)
    if (!data) {
      loadError.value = '账单不存在或加载失败'
      return
    }
    detail.value = data
    const firstUnpaid = payerRows.value.find((r) => !r.paid && r.hasPayUrl)
    const fallback = payerRows.value.find((r) => r.hasPayUrl)
    selectedPayer.value = (firstUnpaid || fallback || payerRows.value[0])?.uid || ''
  } catch (err) {
    loadError.value = `网络错误: ${err}`
  } finally {
    loading.value = false
  }
}

function latestPayUrl(uid) {
  return latestPayUrlByPayer().get(uid)?.payUrl || ''
}

async function pay() {
  const row = selectedRow.value
  if (!row) return ElMessage.warning('请先选择付款人')
  const payUrl = latestPayUrl(row.uid)
  if (!payUrl) return ElMessage.warning('该付款人还没有支付链接，请先在控制台「拉支付链接」')
  paying.value = true
  try {
    if (isMobile) {
      // 手机：直接唤起支付宝客户端收银台
      window.location.href = buildAlipayScheme(payUrl)
      ElMessage.info('正在唤起支付宝…若未响应请确认已安装支付宝')
    } else {
      // PC：展示 scheme 二维码，手机支付宝扫码拉起收银台
      payLink.value = buildAlipayScheme(payUrl)
      qrDataUrl.value = await QRCode.toDataURL(payLink.value, { width: 240, margin: 1 })
      ElMessage.success('请用手机支付宝扫描二维码完成支付')
    }
  } finally {
    paying.value = false
  }
}

async function probe() {
  const row = selectedRow.value
  if (!row) return
  probing.value = true
  try {
    // 后端 CollectRequest 参数：groupBillId + targetUid
    const { body } = await queryPayStatus({ groupBillId: billId, targetUid: row.uid })
    if (body.code === 0) {
      ElMessage.success('已发起支付状态查询，正在刷新…')
      await load()
    } else {
      ElMessage.error(body.msg || '查询失败')
    }
  } finally {
    probing.value = false
  }
}

onMounted(async () => {
  if (!billId) {
    loadError.value = '缺少账单参数：请通过订单查询页的「付款」按钮进入'
    loading.value = false
    return
  }
  await load()
})
</script>

<template>
  <div style="max-width: 520px; margin: 0 auto; padding: 16px">
    <el-card shadow="never">
      <template #header>
        <div style="display:flex; justify-content: space-between; align-items:center">
          <b style="font-size:16px">付款收银台</b>
          <span style="color:#909399; font-size:12px">{{ billId }}</span>
        </div>
      </template>

      <div v-if="loading" style="text-align:center; padding:32px 0">
        <el-icon class="is-loading" :size="28"><i>⌛</i></el-icon>
        <p style="color:#909399">加载账单中…</p>
      </div>

      <div v-else-if="loadError">
        <el-alert type="error" :title="loadError" :closable="false" />
        <el-button style="margin-top:12px" @click="load">重试</el-button>
      </div>

      <template v-else>
        <div style="text-align:center; padding:8px 0 16px">
          <div style="color:#909399; font-size:13px">收款事由</div>
          <div style="font-size:18px; margin:4px 0">{{ model?.remark || '(无备注)' }}</div>
          <div style="font-size:34px; font-weight:700; color:#1677ff">¥{{ model?.totalAmount }}</div>
          <div style="color:#909399; font-size:12px; margin-top:4px">
            {{ paidCount }}/{{ payerRows.length }} 人已支付 · 支付宝群收款
          </div>
        </div>

        <el-divider style="margin:8px 0" />

        <div style="margin:12px 0 6px; color:#606266; font-size:13px">选择付款人</div>
        <el-radio-group v-model="selectedPayer" style="display:flex; flex-direction:column; gap:8px">
          <el-radio v-for="row in payerRows" :key="row.uid" :value="row.uid" style="margin:0; width:100%">
            <div style="display:flex; justify-content:space-between; width:100%; gap:12px">
              <span>UID {{ row.uid }}</span>
              <span>
                <b>¥{{ row.amount }}</b>
                <el-tag v-if="row.paid" type="success" size="small" style="margin-left:6px">已支付</el-tag>
                <el-tag v-else-if="String(row.payStatus) === '1'" type="warning" size="small" style="margin-left:6px">待支付</el-tag>
                <el-tag v-else-if="!row.hasPayUrl" type="info" size="small" style="margin-left:6px">无支付链接</el-tag>
                <el-tag v-else type="info" size="small" style="margin-left:6px">状态{{ row.payStatus }}</el-tag>
              </span>
            </div>
          </el-radio>
        </el-radio-group>

        <el-button
          type="primary"
          size="large"
          style="width:100%; margin-top:20px"
          :loading="paying"
          :disabled="!selectedRow || selectedRow.paid || !selectedRow.hasPayUrl"
          @click="pay"
        >
          {{ isMobile ? '立即支付（唤起支付宝）' : '生成支付二维码' }}
        </el-button>

        <el-button
          style="width:100%; margin-top:10px"
          :loading="probing"
          :disabled="!selectedRow"
          @click="probe"
        >
          刷新支付状态
        </el-button>

        <div v-if="qrDataUrl" style="text-align:center; margin-top:20px">
          <el-divider>手机支付宝扫码支付</el-divider>
          <img :src="qrDataUrl" alt="支付宝支付二维码" style="width:240px; height:240px" />
          <p style="color:#909399; font-size:12px">打开支付宝「扫一扫」，识别后将在支付宝内完成支付</p>
          <el-link type="primary" :href="payLink">{{ payLink.slice(0, 60) }}…</el-link>
        </div>

        <p style="color:#c0c4cc; font-size:11px; margin-top:16px; text-align:center">
          支付由支付宝完成，本页仅唤起收银台与查询状态
        </p>
      </template>
    </el-card>
  </div>
</template>
