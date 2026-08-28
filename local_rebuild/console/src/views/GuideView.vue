<script setup>
const origin = typeof location !== 'undefined' ? location.origin : 'http://<服务器>:18722'
const steps = [
  { title: '装克隆钉钉', desc: '手机安装 dingtalk-localtest.apk（包名 .localtest）' },
  { title: '二次唤醒注册', desc: '打开 App → Home → 再切回来，WS 才会注册' },
  { title: '绑定角色', desc: '控制台「设备管理」把收款账号绑主号、付款账号绑子号' },
  { title: '群里发起收款', desc: '在钉钉群发一笔群收款，钩子会上报账单' },
  { title: '拉支付链接', desc: '订单查询点「拉支付链接」，或走收款指令页' },
  { title: '收银台付款', desc: '点「付款」进入收银台，手机唤起支付宝 / PC 扫码' },
]
</script>

<template>
  <div class="guide">
    <el-alert type="success" :closable="false" style="margin-bottom: 16px">
      <template #title><b>群收款 Mock 操作教程</b></template>
      这套系统用改包克隆钉钉把群收款账单、支付链接、付款状态报到本控制台。
      <b>多笔账单可以并存</b>，每次拉链接 / 付款都是针对<strong>当前这一笔</strong>。
    </el-alert>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>整体流程</b></template>
      <el-steps :active="5" finish-status="success" align-center>
        <el-step v-for="s in steps" :key="s.title" :title="s.title" :description="s.desc" />
      </el-steps>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>手机端操作（必读）</b></template>
      <el-alert type="error" :closable="false" style="margin-bottom: 12px">
        <template #title>三条红线</template>
        ① 这是<strong>真实扣款</strong>，不是模拟；② 克隆包仅用于测试，别当日常钉钉用；③ 别在同一手机短时间连点两笔「立即支付」。
      </el-alert>

      <el-divider content-position="left">A. 安装与启动</el-divider>
      <ol class="ol">
        <li>把 <code>dingtalk-localtest.apk</code> 传到手机安装（可用 <code>adb install</code> 或文件管理器）。</li>
        <li>首次打开，登录测试账号。</li>
        <li>系统弹「通知已关闭」「悬浮窗权限」等提示，按引导允许即可（悬浮窗用于顶部状态条）。</li>
      </ol>

      <el-divider content-position="left">B. 二次唤醒（最关键，漏了设备不上线）</el-divider>
      <el-alert type="warning" :closable="false" style="margin-bottom: 8px">
        钩子只在<b>第二次 onResume</b> 才连服务器。装完打开一次不算。
      </el-alert>
      <ol class="ol">
        <li>打开克隆钉钉（停留在首页）。</li>
        <li>按 <b>Home 键</b>回桌面。</li>
        <li>再点图标切回克隆钉钉。</li>
        <li>看顶部是否出现绿色状态条「V2.x-test … 在线」；控制台「设备管理」应出现你的 uid。</li>
      </ol>

      <el-divider content-position="left">C. 在群里发起收款</el-divider>
      <ol class="ol">
        <li>进目标群 → 点输入框旁「+」→ 选「群收款」。</li>
        <li>填金额、选人（可均分 / 指定人）、填备注，发起。</li>
        <li>发起后控制台「订单查询」会出现这笔账单（状态「待拉链接」）。</li>
      </ol>

      <el-divider content-position="left">D. 付款</el-divider>
      <ol class="ol">
        <li>控制台把这笔「拉支付链接」→ 状态变「已拉链接」。</li>
        <li>手机浏览器打开收银台链接（或 PC 生成二维码用手机扫）。</li>
        <li>点「立即支付」→ 唤起支付宝 → 核对金额 → 输密码。</li>
        <li>付完回控制台强刷，订单变「已付款」。</li>
      </ol>

      <el-divider content-position="left">E. 手机端注意事项</el-divider>
      <ul class="ul">
        <li><b>账号互踢</b>：克隆包和正式版钉钉不要同时登同一个号，会互相挤掉。</li>
        <li><b>别连点</b>：一笔付完再付下一笔；同时点两笔可能串单。</li>
        <li><b>群收款页打不开/白屏</b>：说明 APK 没带 UC 绕过，需重新构建（加 <code>--uc-auth-bypass</code>）。</li>
        <li><b>付了款订单没变</b>：在钉钉里打开那笔账单让它同步一次，再看控制台。</li>
        <li><b>换手机/重装</b>：要重新做一遍「二次唤醒」，并重新 enroll 拿密钥。</li>
      </ul>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>1. 控制台首页</b></template>
      <p class="hint">左侧菜单：设备 → 收款指令 → 事件流 → 订单查询 → 日志 → API → 本教程。</p>
      <img class="shot" src="/guide/01_console.png" alt="控制台首页：设备管理" />
      <el-descriptions :column="2" border size="small" style="margin-top: 12px">
        <el-descriptions-item label="设备管理">看手机是否在线、绑定主号/子号</el-descriptions-item>
        <el-descriptions-item label="收款指令">手动下发拉链接 / 查详情 / 查支付状态</el-descriptions-item>
        <el-descriptions-item label="订单查询">所有群收款账单列表，点「付款」进收银台</el-descriptions-item>
        <el-descriptions-item label="事件流">bill.upsert / alipay.upload / mark_paid 原始上报</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>2. 手机注册（最容易漏）</b></template>
      <el-alert type="warning" :closable="false" style="margin-bottom: 12px">
        钩子要 <b>第二次 onResume</b> 才会连 WebSocket。装完打开一次不够。
      </el-alert>
      <ol class="ol">
        <li>安装 <code>dingtalk-localtest.apk</code>，打开并登录。</li>
        <li>按 <b>Home</b> 回到桌面。</li>
        <li>再点图标切回克隆钉钉。</li>
        <li>本页「设备管理」应出现你的 uid（例如 199504987），状态在线。</li>
      </ol>
      <p class="hint">设备首次连上会自动 <code>/api/device/enroll</code>，服务器下发 HMAC 密钥（RSA 加密），之后支付通知会签名 + 混合加密上报。</p>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>3. 在群里发起收款</b></template>
      <p>用克隆钉钉进目标群 → 发起群收款（可均分、可指定人）。一笔账单一个 <code>groupBillId</code>。</p>
      <ul class="ul">
        <li><b>同一群多笔收款</b>：支持。每笔独立出现在订单列表，互不影响。</li>
        <li><b>同一笔多人分摊</b>：支持。支付凭证是 <code>账单ID_付款人UID</code>。</li>
        <li><b>不要</b>在同一手机上短时间连点两笔「立即支付」（钩子有全局 pendingBillId，可能串单）。</li>
      </ul>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>4. 订单查询：拉链接 + 付款</b></template>
      <img class="shot" src="/guide/02_orders.png" alt="订单查询：账单列表与付款按钮" />
      <el-table :data="[
        { col: '待拉链接', mean: '账单已上报，还没有支付宝订单串' },
        { col: '已拉链接', mean: '已拿到 payUrl（orderStr），可以进收银台' },
        { col: '已付款', mean: '收到过 mark_paid 凭证（按 pay_id 前缀匹配账单）' },
      ]" size="small" border style="margin-top: 12px">
        <el-table-column prop="col" label="状态" width="120" />
        <el-table-column prop="mean" label="含义" />
      </el-table>
      <ol class="ol">
        <li>找到刚发起的账单，点蓝色「拉支付链接」（或到「收款指令」页填账单 ID + 子号 UID）。</li>
        <li>状态变为「已拉链接」后，点绿色「付款」——新标签打开收银台。</li>
        <li>「详情」可看原始 groupBillItem / 事件。</li>
      </ol>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>5. 收银台（真实支付宝）</b></template>
      <img class="shot shot-narrow" src="/guide/03_cashier.png" alt="付款收银台" />
      <ul class="ul">
        <li><b>手机浏览器</b>：点「立即支付」→ 唤起支付宝 App（scheme <code>alipays://…orderSuffix=</code>）。</li>
        <li><b>电脑浏览器</b>：点「生成支付二维码」→ 手机扫短链 → 手机页自动唤起支付宝。真实 orderStr 太长，不能直接做成二维码。</li>
        <li>每人一行：待支付 / 已支付。已支付来自 <code>mark_paid</code> 或 <code>payStatus=2</code>。<code>payStatus=1</code> 是创建时默认，<b>不是已付</b>。</li>
        <li>这是<strong>真扣款</strong>，核对金额后再输密码。</li>
      </ul>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>6. 付款后怎么确认</b></template>
      <ol class="ol">
        <li>订单查询强刷（Ctrl+Shift+R）：该账单应变为「已付款」。</li>
        <li>事件流过滤 <code>mark_paid</code>：应有 <code>pay_id = 账单ID_你的UID</code>。</li>
        <li>再进收银台：对应付款人显示绿色「已支付」，例如 1/2 人已支付。</li>
      </ol>
      <el-alert type="info" :closable="false">
        「刷新支付状态」走的是钉钉 probe 接口，当前钩子是旁听模式，点了会超时。以 <code>mark_paid</code> 和强刷订单页为准。
      </el-alert>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><b>7. 加密自测（不真扣款）</b></template>
      <p>验证手机上报是否已签名 + RSA/AES 加密，不经过支付宝：</p>
      <pre class="code">curl -X POST {{ origin }}/api/admin/crypto-selftest \
  -H 'Content-Type: application/json' \
  -d '{"groupBillId":"x","targetUid":"你的uid","timeoutSeconds":20}'</pre>
      <p class="hint">成功应返回 <code>signed: true, encrypted: true</code>。设备必须已在线（完成第 2 步）。</p>
    </el-card>

    <el-card shadow="never">
      <template #header><b>常见问题</b></template>
      <el-collapse>
        <el-collapse-item title="设备列表看不到手机">
          再做一次 Home → 切回。看事件流有没有 <code>register</code> / <code>ack</code>。
        </el-collapse-item>
        <el-collapse-item title="群收款页打不开 / 白屏">
          APK 必须带 UC 鉴权绕过（构建加 <code>--uc-auth-bypass</code>）。没这个会 OPEN_FAIL_UC_FAIL。
        </el-collapse-item>
        <el-collapse-item title="订单显示已付款，但收银台还是待支付">
          旧版把 payStatus=1 当成已付。强刷页面；已付款以 mark_paid 为准。
        </el-collapse-item>
        <el-collapse-item title="付了款但订单还是已拉链接">
          旧 bug 已修（pay_id 按账单 ID 前缀匹配）。仍不对就看事件流有没有该账单的 mark_paid；没有则打开钉钉里那笔账单让 App 同步一次。
        </el-collapse-item>
        <el-collapse-item title="PC 点支付没反应 / 二维码出不来">
          真实订单串超过二维码容量。用现在的短链二维码；手机打开后再唤起支付宝。
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<style scoped>
.guide { max-width: 960px; }
.shot {
  display: block;
  width: 100%;
  max-width: 880px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin: 8px 0 4px;
}
.shot-narrow { max-width: 420px; }
.hint { color: #606266; font-size: 13px; margin: 8px 0 0; }
.ol, .ul { line-height: 1.7; padding-left: 20px; }
.code {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
}
</style>
