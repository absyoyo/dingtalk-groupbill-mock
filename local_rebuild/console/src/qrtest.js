import QRCode from 'qrcode'
window.QRCode = QRCode
document.getElementById('s').textContent = 'ready:' + typeof QRCode?.toDataURL
