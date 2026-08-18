<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchDevices, fetchBills, sendAdminMessage, collectPayUrl, queryDetail, queryPayStatus } from '../api'
import { ElMessage } from 'element-plus'

const devices = ref([])
const bills = ref([])

const slaveDevices = computed(() => devices.value.filter((d) => d.role !== 'master'))
const masterDevices = computed(() => devices.value.filter((d) => d.role === 'master'))

const load = async () => {
  const [devBody, billBody] = await Promise.all([fetchDevices(), fetchBills({ page: 1, size: 100 })])
  devices.value = devBody.devices
  bills.value = billBody.items || []
}

onMounted(load)

const presetBill = ref('')
const presetTarget = ref('')
const applyPreset = (bill, target) => {
  presetBill.value = bill
  presetTarget.value = target
}

const collectForm = ref({ groupBillId: '', targetUid: '', creatorUid: '', timeoutSeconds: 30 })
const detailForm = ref({ groupBillId: '', targetUid: '', creatorUid: '', timeoutSeconds: 30 })
const probeForm = ref({ groupBillId: '', targetUid: '', creatorUid: '', timeoutSeconds: 30 })

const collectLoading = ref(false)
const detailLoading = ref(false)
const probeLoading = ref(false)
const collectResult = ref(null)
const detailResult = ref(null)
const probeResult = ref(null)

const runCollect = async () => {
  if (!collectForm.value.groupBillId || !collectForm.value.targetUid) {
    ElMessage.error('账单ID和目标子号UID必填')
    return
  }
  collectLoading.value = true
  collectResult.value = null
  try {
    const payload = { ...collectForm.value }
    if (!payload.creatorUid) delete payload.creatorUid
    const { body } = await collectPayUrl(payload)
    if (body.code === 0) {
      collectResult.value = body.data
      ElMessage.success(`收到支付链接 (payUrl 长度 ${body.data.payUrl?.length || 0})`)
    } else ElMessage.error(body.msg)
  } finally {
    collectLoading.value = false
  }
}

const runDetail = async () => {
  if (!detailForm.value.groupBillId || !detailForm.value.targetUid) {
    ElMessage.error('账单ID和目标子号UID必填')
    return
  }
  detailLoading.value = true
  detailResult.value = null
  try {
    const payload = { ...detailForm.value }
    if (!payload.creatorUid) delete payload.creatorUid
    const { body } = await queryDetail(payload)
    if (body.code === 0) {
      detailResult.value = body.data
      ElMessage.success('已收到账单详情')
    } else ElMessage.error(body.msg)
  } finally {
    detailLoading.value = false
  }
}

const runProbe = async () => {
  if (!probeForm.value.groupBillId || !probeForm.value.targetUid) {
    ElMessage.error('账单ID和目标子号UID必填')
    return
  }
  probeLoading.value = true
  probeResult.value = null
  try {
    const payload = { ...probeForm.value }
    if (!payload.creatorUid) delete payload.creatorUid
    const { body } = await queryPayStatus(payload)
    if (body.code === 0) {
      probeResult.value = body.data
      ElMessage.success('已收到支付状态')
    } else ElMessage.error(body.msg)
  } finally {
    probeLoading.value = false
  }
}

const target = ref('')
const messageType = ref('bill.task')
const payloadText = ref('{}')
const types = [
  { value: 'bill.task', label: '收款指令（拉支付链接）', desc: '让子号主动调钉钉 payGroupBill RPC 拉取支付串，回调 alipay.upload' },
  { value: 'orders.follow', label: '订单关注列表', desc: '下发给子号一批账单ID，让子号持续监控这些账单的支付状态' },
  { value: 'bill.done', label: '账单结束通知', desc: '通知子号某笔账单已结束，停止监控并释放 SdkFollowKeeper 资源' },
  { value: 'rpc.call', label: '远程RPC调用', desc: '让子号反射调用钉钉内部 RPC（queryGroupBillDetail/syncGroupBillPayStatus 等），回调 rpc.result' },
  { value: 'alipay.result', label: '支付结果通知', desc: '通知子号支付结果状态（已支付/未支付/失败），触发 onAlipayResult 回调' },
]
const currentTypeDesc = computed(() => types.find((t) => t.value === messageType.value)?.desc || '')

const send = async () => {
  let data
  try {
    data = JSON.parse(payloadText.value)
  } catch {
    ElMessage.error('JSON 格式错误')
    return
  }
  const body = { type: messageType.value, data }
  if (target.value) body.userId = target.value
  const { status, body: result } = await sendAdminMessage(body)
  if (result.code === 0) ElMessage.success(`已发送到: ${(result.data?.delivered || []).join(', ')}`)
  else ElMessage.error(`发送失败: ${result.msg || status}`)
}

const presetCollect = (bill) => {
  collectForm.value.groupBillId = bill.groupBillId
  collectForm.value.creatorUid = bill.creatorUid
}
</script>

<template>
  <div style="display: flex; flex-direction: column; gap: 20px">
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><b>① 拉支付链接</b> — bill.task → alipay.upload</template>
          <el-form label-width="120px" size="small">
            <el-form-item label="账单">
              <el-select v-model="collectForm.groupBillId" filterable placeholder="选账单" @change="(v) => presetCollect(bills.find((b) => b.groupBillId === v))" style="width: 100%">
                <el-option v-for="b in bills" :key="b.groupBillId" :label="`${b.groupBillId} (${b.creatorUid})`" :value="b.groupBillId" />
              </el-select>
            </el-form-item>
            <el-form-item label="目标子号">
              <el-select v-model="collectForm.targetUid" filterable allow-create placeholder="选子号设备" style="width: 100%">
                <el-option v-for="d in slaveDevices" :key="d.userId" :label="`${d.userId} (${d.accountId})`" :value="d.userId" />
              </el-select>
            </el-form-item>
            <el-form-item label="创建者UID">
              <el-input v-model="collectForm.creatorUid" placeholder="留空则默认等于目标UID" />
            </el-form-item>
            <el-form-item label="超时(秒)">
              <el-input-number v-model="collectForm.timeoutSeconds" :min="3" :max="120" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="collectLoading" @click="runCollect">执行</el-button>
            </el-form-item>
          </el-form>
          <el-descriptions v-if="collectResult" :column="1" border size="small">
            <el-descriptions-item label="groupBillId">{{ collectResult.groupBillId }}</el-descriptions-item>
            <el-descriptions-item label="payId">{{ collectResult.payId }}</el-descriptions-item>
            <el-descriptions-item label="payerUid">{{ collectResult.payerUid }}</el-descriptions-item>
            <el-descriptions-item label="支付链接">
              <el-input type="textarea" :rows="4" readonly :model-value="collectResult.payUrl" />
              <el-button size="small" text type="primary" @click="navigator.clipboard.writeText(collectResult.payUrl).then(() => ElMessage.success('已复制'))">复制</el-button>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><b>② 查账单详情</b> — rpc.call detail → rpc.result</template>
          <el-form label-width="120px" size="small">
            <el-form-item label="账单">
              <el-select v-model="detailForm.groupBillId" filterable placeholder="选账单" style="width: 100%">
                <el-option v-for="b in bills" :key="b.groupBillId" :label="`${b.groupBillId} (${b.creatorUid})`" :value="b.groupBillId" />
              </el-select>
            </el-form-item>
            <el-form-item label="目标子号">
              <el-select v-model="detailForm.targetUid" filterable allow-create placeholder="选子号设备" style="width: 100%">
                <el-option v-for="d in slaveDevices" :key="d.userId" :label="`${d.userId} (${d.accountId})`" :value="d.userId" />
              </el-select>
            </el-form-item>
            <el-form-item label="创建者UID">
              <el-input v-model="detailForm.creatorUid" placeholder="留空则默认等于目标UID" />
            </el-form-item>
            <el-form-item label="超时(秒)">
              <el-input-number v-model="detailForm.timeoutSeconds" :min="3" :max="120" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="detailLoading" @click="runDetail">执行</el-button>
            </el-form-item>
          </el-form>
          <pre v-if="detailResult" style="white-space: pre-wrap; font-family: monospace; font-size: 11px; max-height: 240px; overflow: auto">{{ JSON.stringify(detailResult, null, 2) }}</pre>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><b>③ 查支付状态</b> — rpc.call probePayStatus → rpc.result</template>
          <el-form label-width="120px" size="small">
            <el-form-item label="账单">
              <el-select v-model="probeForm.groupBillId" filterable placeholder="选账单" style="width: 100%">
                <el-option v-for="b in bills" :key="b.groupBillId" :label="`${b.groupBillId} (${b.creatorUid})`" :value="b.groupBillId" />
              </el-select>
            </el-form-item>
            <el-form-item label="目标子号">
              <el-select v-model="probeForm.targetUid" filterable allow-create placeholder="选子号设备" style="width: 100%">
                <el-option v-for="d in slaveDevices" :key="d.userId" :label="`${d.userId} (${d.accountId})`" :value="d.userId" />
              </el-select>
            </el-form-item>
            <el-form-item label="创建者UID">
              <el-input v-model="probeForm.creatorUid" placeholder="留空则默认等于目标UID" />
            </el-form-item>
            <el-form-item label="超时(秒)">
              <el-input-number v-model="probeForm.timeoutSeconds" :min="3" :max="120" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="probeLoading" @click="runProbe">执行</el-button>
            </el-form-item>
          </el-form>
          <pre v-if="probeResult" style="white-space: pre-wrap; font-family: monospace; font-size: 11px; max-height: 240px; overflow: auto">{{ JSON.stringify(probeResult, null, 2) }}</pre>
        </el-card>
      </el-col>
    </el-row>

    <el-collapse>
      <el-collapse-item title="高级 — 通用消息下发（手填 JSON）" name="advanced">
        <el-form label-width="100px">
          <el-form-item label="目标设备">
            <el-select v-model="target" clearable placeholder="不选则广播全部" style="width: 420px">
              <el-option v-for="d in devices" :key="d.userId" :label="`${d.userId} (${d.role})`" :value="d.userId" />
            </el-select>
          </el-form-item>
          <el-form-item label="消息类型">
            <el-select v-model="messageType" style="width: 100%">
              <el-option v-for="t in types" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
            <div style="font-size: 12px; color: #909399; margin-top: 4px">{{ currentTypeDesc }}</div>
          </el-form-item>
          <el-form-item label="消息内容">
            <el-input v-model="payloadText" type="textarea" :rows="6" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="send">发送</el-button>
          </el-form-item>
        </el-form>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>
