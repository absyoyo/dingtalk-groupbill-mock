const base = ''

async function request(url, options) {
  const res = await fetch(url, options)
  const body = await res.json()
  return { status: res.status, body }
}

export async function fetchDevices() {
  const { body } = await request(`${base}/api/admin/devices`)
  return body.code === 0 ? body.data : { devices: [] }
}

export async function fetchEvents(params) {
  const query = new URLSearchParams(params).toString()
  const { body } = await request(`${base}/api/admin/events?${query}`)
  return body.code === 0 ? body.data : { total: 0, items: [] }
}

export async function fetchOrders(params) {
  const query = new URLSearchParams(params).toString()
  const { body } = await request(`${base}/api/admin/orders?${query}`)
  return body.code === 0 ? body.data : { total: 0, items: [] }
}

export async function fetchBills(params) {
  const query = new URLSearchParams(params).toString()
  const { body } = await request(`${base}/api/admin/bills?${query}`)
  return body.code === 0 ? body.data : { total: 0, items: [] }
}

export async function fetchBillDetail(groupBillId) {
  const { body } = await request(`${base}/api/admin/bills/${encodeURIComponent(groupBillId)}`)
  return body.code === 0 ? body.data : null
}

export async function sendAdminMessage(payload) {
  const { status, body } = await request(`${base}/api/admin/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return { status, body }
}

export async function kickDevice(userId) {
  const { status, body } = await request(`${base}/api/admin/devices/${userId}`, { method: 'DELETE' })
  return { status, body }
}

export async function setDeviceRole(userId, role) {
  const { status, body } = await request(`${base}/api/admin/devices/${userId}/role`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role }),
  })
  return { status, body }
}

export async function collectPayUrl(payload) {
  const { status, body } = await request(`${base}/api/admin/collect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return { status, body }
}

export async function queryDetail(payload) {
  const { status, body } = await request(`${base}/api/admin/query-detail`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return { status, body }
}

export async function queryPayStatus(payload) {
  const { status, body } = await request(`${base}/api/admin/query-pay-status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return { status, body }
}

export async function fetchServerLogs(params) {
  const query = new URLSearchParams(params).toString()
  const { body } = await request(`${base}/api/admin/logs?${query}`)
  return body.code === 0 ? body.data : { total: 0, items: [] }
}

export async function fetchLogcat(params) {
  const query = new URLSearchParams(params).toString()
  const { body } = await request(`${base}/api/admin/logcat?${query}`)
  return body.code === 0 ? body.data : { total: 0, items: [] }
}

export async function toggleLogcat() {
  const { status, body } = await request(`${base}/api/admin/logcat/toggle`, { method: 'POST' })
  return { status, body }
}

export function openAdminStream(onEvent) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const socket = new WebSocket(`${proto}://${location.host}/api/admin/ws`)
  socket.onmessage = (message) => onEvent(JSON.parse(message.data))
  return socket
}
