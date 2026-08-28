import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import CashierView from './CashierView.vue'

createApp(CashierView).use(ElementPlus).mount('#cashier')
