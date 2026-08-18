# 公网部署指南

把本地开发环境部署到公网服务器，让手机通过 4G/WiFi 连接公网域名访问后端。

## 部署架构

```
手机 (4G/WiFi)
    │  HTTPS / WSS
    ▼
┌─────────────────────────────────┐
│  Nginx 443 (HTTPS + WSS 反代)   │  ← 公网入口
│  · HTTP→HTTPS 301              │
│  · /ws, /api/admin/ws 升级 WSS │
│  · /api/admin/* 限流            │
│  · /docs /redoc basic auth      │
└────────────┬────────────────────┘
             │  127.0.0.1:18722
             ▼
┌─────────────────────────────────┐
│  uvicorn (systemd 托管)          │  ← loopback only
│  · FastAPI + 前端静态托管        │
│  · API_KEY 鉴权                  │
└─────────────────────────────────┘
```

## 前置准备清单

| 项 | 要求 |
|----|------|
| 服务器 | 公网云主机（Ubuntu 22.04+ / Debian 12+） |
| 域名 | 已 A 记录解析到服务器公网 IP |
| 端口 | 80 / 443 在防火墙/安全组放行 |
| 代码 | 项目已上传到 `/opt/dingtalk-mock`（或自定义路径） |
| sudo | 当前用户有 sudo 权限 |

## 一键部署

```bash
sudo DEPLOY_DOMAIN=bill.example.com \
     DEPLOY_EMAIL=you@example.com \
     ./deploy/deploy.sh
```

脚本自动完成：装系统依赖 → 装 Python 包 → 构建前端 → 生成 API Key → 配置 systemd → 配置 Nginx → 申请 Let's Encrypt 证书 → 配置防火墙。

部署完成后会输出：
- 域名、Swagger 地址、控制台地址
- 自动生成的 API Key（32 字符随机）
- APK 后端 URL（用于重新打包）

## 手动步骤（如需细控）

### 1. 上传项目代码

```bash
# 本地打包
rsync -avz --exclude='node_modules' --exclude='__pycache__' \
  dingtalk_check_fn_analysis_20260809/ \
  user@server:/opt/dingtalk-mock/

# 或用 git clone
```

### 2. 安装依赖

```bash
sudo apt update
sudo apt install -y python3 python3-pip nginx certbot python3-certbot-nginx
pip3 install --break-system-packages fastapi uvicorn[standard] pydantic
```

### 3. 构建前端（如未在本地构建）

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
sudo apt install -y nodejs
cd /opt/dingtalk-mock/local_rebuild/console
npm install && npm run build
```

### 4. 配置 systemd

```bash
sudo cp /opt/dingtalk-mock/deploy/dingtalk-mock.service /etc/systemd/system/
# 编辑文件，替换 PROJECT_DIR 和 API_KEY
sudo vim /etc/systemd/system/dingtalk-mock.service
sudo systemctl daemon-reload
sudo systemctl enable --now dingtalk-mock
sudo systemctl status dingtalk-mock  # 验证 running
```

### 5. 配置 Nginx + HTTPS

```bash
sudo cp /opt/dingtalk-mock/deploy/nginx.conf /etc/nginx/sites-available/dingtalk-mock
sudo ln -sf /etc/nginx/sites-available/dingtalk-mock /etc/nginx/sites-enabled/
sudo vim /etc/nginx/sites-available/dingtalk-mock  # 替换 SERVER_NAME
sudo nginx -t && sudo systemctl reload nginx

# 申请 SSL 证书
sudo certbot --nginx -d bill.example.com --non-interactive \
  --agree-tos -m you@example.com --redirect
```

### 6. 防火墙

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 18722/tcp   # 关闭直连，强制走 Nginx
sudo ufw --force enable
```

## 安全加固

### 1. API Key 鉴权（必开）

```bash
# 生成强随机 key
openssl rand -hex 24
# 设到 systemd service 的 Environment=API_KEY=...
sudo systemctl edit dingtalk-mock  # 或改 service 文件
sudo systemctl restart dingtalk-mock
```

调用方请求头：`X-API-Key: <生成的 key>`

### 2. /docs /redoc 保护

Nginx 配置已带 basic auth（注释里有），生成密码文件：
```bash
sudo htpasswd -c /etc/nginx/.htpasswd-dingtalk admin
sudo systemctl reload nginx
```

### 3. 限流

Nginx 配置已带 `limit_req zone=admin_api rate=10r/s burst=20`，按 IP 限流。

### 4. fail2ban（防暴力破解）

```bash
sudo apt install -y fail2ban
sudo cat > /etc/fail2ban/jail.d/dingtalk.conf <<EOF
[dingtalk-429]
enabled = true
filter = dingtalk-429
logpath = /var/log/nginx/dingtalk-mock.error.log
maxretry = 50
bantime = 3600
EOF
```

### 5. 关闭直连 18722

systemd 里 uvicorn 绑 `--host 127.0.0.1`，Nginx 反代，公网无法直连。

## APK 端适配

公网部署后，APK 内嵌的后端 URL 必须改成 `https://bill.example.com`：

```bash
./dingtalk_check_fn_analysis_20260809/local_rebuild/scripts/build_for_backend.sh \
  https://bill.example.com
```

打包后 APK 自动：
- HTTP base: `https://bill.example.com`
- WebSocket URL: `wss://bill.example.com/ws`（HTTPS 对应 WSS，钉钉 hook 的 `wsUrlFromHttpBase` 自动转换）

安装到手机，手机通过 4G/WiFi 连接公网域名。

## 本地开发 vs 公网部署 差异

| 项 | 本地开发 | 公网部署 |
|----|---------|---------|
| 后端 URL | `http://192.168.8.200:18722` | `https://bill.example.com` |
| WS 协议 | `ws://` | `wss://` |
| 手机连接 | 同局域网 | 任意网络（4G/WiFi） |
| API Key | 未启用（开放） | 必须启用 |
| logcat 采集 | adb 直连手机 | 不可用（手机不在服务器旁） |
| 进程管理 | `./run.sh start` 前台 | systemd 托管，开机自启 |
| HTTPS | 无（HTTP） | Let's Encrypt 自动续期 |

## logcat 采集说明

公网部署后服务器没有 adb 直连手机，`/api/admin/logcat/toggle` 接口不可用（adb 找不到设备）。
查看手机端日志的替代方案：
1. **手机端 logcat 落盘 + 上报**：需要在 APK 里加日志上报 hook（APK 改造）
2. **adb over WiFi**：手机开启 WiFi 调试，服务器 adb connect 手机 IP（要求手机和服务器同网或在公网可路由）
3. **手机本地查看**：用手机 logcat App 或 `adb logcat` 现场

## 运维命令

```bash
# 查看服务状态
sudo systemctl status dingtalk-mock

# 实时日志
sudo journalctl -u dingtalk-mock -f

# 重启
sudo systemctl restart dingtalk-mock

# Nginx 日志
sudo tail -f /var/log/nginx/dingtalk-mock.access.log

# 证书续期（certbot 自动，手动测试）
sudo certbot renew --dry-run

# 查看在线设备
curl -H "X-API-Key: <key>" https://bill.example.com/api/admin/devices
```

## 故障排查

| 症状 | 排查 |
|------|------|
| 手机连不上 WS | 1. 域名 DNS 是否解析？2. 443 是否开放？3. Nginx 配置 `proxy_read_timeout` 是否够长？ |
| WSS 握手失败 | Nginx 的 `location ~ ^/(ws\|api/admin/ws)$` 是否正确升级？ |
| API 401 | X-API-Key 头是否正确？systemd service 的 API_KEY 是否设置？ |
| /docs 401 | Nginx basic auth 的 `.htpasswd-dingtalk` 文件是否创建？ |
| 502 | uvicorn 是否在跑？端口 127.0.0.1:18722 是否监听？ |
| 证书过期 | `sudo certbot renew` 自动续期；检查 systemd 的 certbot.timer |
