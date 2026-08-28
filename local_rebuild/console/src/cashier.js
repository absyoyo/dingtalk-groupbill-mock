import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import CashierView from './CashierView.vue'
export { default as QRCode } from 'qrcode'
createApp(CashierView).use(ElementPlus).mount('#cashier')
