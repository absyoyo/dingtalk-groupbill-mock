#!/usr/bin/env bash
# 一键部署到公网服务器（在服务器上执行）
#
# 用法：
#   sudo DEPLOY_DOMAIN=bill.example.com DEPLOY_EMAIL=you@example.com \
#     DEPLOY_API_KEY=$(openssl rand -hex 24) \
#     ./deploy.sh
#
# 前置条件：
#   - Ubuntu 22.04+ / Debian 12+ 公网服务器
#   - 域名已 A 记录解析到本机公网 IP
#   - 80/443 端口在防火墙/安全组放行
#   - 当前用户有 sudo 权限
#   - 项目代码已上传到 $PROJECT_DIR（默认 /opt/dingtalk-mock）

set -euo pipefail

# ── 配置（环境变量覆盖） ──────────────────────────────────────────────
PROJECT_DIR="${PROJECT_DIR:-/opt/dingtalk-mock}"
DEPLOY_DOMAIN="${DEPLOY_DOMAIN:-}"        # 必填，如 bill.example.com
DEPLOY_EMAIL="${DEPLOY_EMAIL:-}"          # 用于 Let us Encrypt 注册
DEPLOY_API_KEY="${DEPLOY_API_KEY:-}"      # 不填则自动生成
SERVICE_USER="${SERVICE_USER:-www-data}"
SERVICE_NAME="dingtalk-mock"

if [[ -z "$DEPLOY_DOMAIN" ]]; then
  printf '错误：DEPLOY_DOMAIN 必填，如 bill.example.com\n' >&2
  exit 2
fi

# ── 1. 安装系统依赖 ──────────────────────────────────────────────────
printf '[1/8] 安装系统依赖...\n'
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-pip nginx certbot python3-certbot-nginx \
  ufw curl jq openssl

# ── 2. 安装 Python 依赖 ─────────────────────────────────────────────
printf '[2/8] 安装 Python 依赖...\n'
pip3 install --quiet --break-system-packages fastapi uvicorn[standard] pydantic

# ── 3. 构建前端（若未构建） ─────────────────────────────────────────
if [[ ! -f "$PROJECT_DIR/local_rebuild/server/static/index.html" ]]; then
  printf '[3/8] 构建前端...\n'
  if ! command -v npm >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y -qq nodejs
  fi
  (cd "$PROJECT_DIR/local_rebuild/console" && npm install --silent && npm run build)
else
  printf '[3/8] 前端已构建，跳过\n'
fi

# ── 4. 生成 API Key（若未提供） ────────────────────────────────────
if [[ -z "$DEPLOY_API_KEY" ]]; then
  DEPLOY_API_KEY="$(openssl rand -hex 24)"
fi
printf '[4/8] API Key: %s\n' "$DEPLOY_API_KEY"

# ── 5. 配置 systemd service ────────────────────────────────────────
printf '[5/8] 配置 systemd service...\n'
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
sed -e "s|PROJECT_DIR|$PROJECT_DIR|g" \
    -e "s|User=www-data|User=$SERVICE_USER|" \
    -e "s|Group=www-data|Group=$SERVICE_USER|" \
    -e "s|Environment=API_KEY=CHANGE-ME-TO-RANDOM-32-CHARS|Environment=API_KEY=$DEPLOY_API_KEY|" \
    "$PROJECT_DIR/deploy/dingtalk-mock.service" >"$SERVICE_FILE"

# 确保 logs 目录存在且服务用户可写
mkdir -p "$PROJECT_DIR/local_rebuild/logs" "$PROJECT_DIR/local_rebuild/dist"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/local_rebuild/logs"

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

# ── 6. 配置 Nginx + HTTPS ───────────────────────────────────────────
printf '[6/8] 配置 Nginx...\n'
NGINX_SITE="/etc/nginx/sites-available/${SERVICE_NAME}"
sed "s|SERVER_NAME|$DEPLOY_DOMAIN|g" \
    "$PROJECT_DIR/deploy/nginx.conf" >"$NGINX_SITE"
ln -sf "$NGINX_SITE" "/etc/nginx/sites-enabled/${SERVICE_NAME}"
rm -f /etc/nginx/sites-enabled/default

# 先用 HTTP 配置起 Nginx，方便 certbot 挑战
sed -i 's/listen 443 ssl http2;/listen 80;/; /ssl_.*;/d; /add_header Strict-Transport/d' "$NGINX_SITE" 2>/dev/null || true
nginx -t && systemctl reload nginx

# ── 7. 申请 Let us Encrypt 证书 ─────────────────────────────────────
if [[ -n "$DEPLOY_EMAIL" ]]; then
  printf '[7/8] 申请 Let us Encrypt 证书...\n'
  certbot --nginx -d "$DEPLOY_DOMAIN" --non-interactive --agree-tos -m "$DEPLOY_EMAIL" --redirect
  # certbot 会自动改写 nginx 配置加 SSL，再 reload
else
  printf '[7/8] 跳过证书申请（未提供 DEPLOY_EMAIL）— 请手动用 certbot 或上传证书\n'
fi

# 恢复完整 Nginx 配置（含 443 SSL + 80→443 跳转）
sed "s|SERVER_NAME|$DEPLOY_DOMAIN|g" \
    "$PROJECT_DIR/deploy/nginx.conf" >"$NGINX_SITE"
nginx -t && systemctl reload nginx

# ── 8. 防火墙 + 收尾 ───────────────────────────────────────────────
printf '[8/8] 配置防火墙...\n'
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 关闭 18722 直连（只允许 Nginx 反代）
ufw deny 18722/tcp 2>/dev/null || true

printf '\n✅ 部署完成！\n'
printf '────────────────────────────────────────────\n'
printf '域名:       https://%s\n' "$DEPLOY_DOMAIN"
printf 'Swagger:    https://%s/docs\n' "$DEPLOY_DOMAIN"
printf '控制台:     https://%s/\n' "$DEPLOY_DOMAIN"
printf 'API Key:    %s\n' "$DEPLOY_API_KEY"
printf 'APK 后端URL: https://%s\n' "$DEPLOY_DOMAIN"
printf '日志:        journalctl -u %s -f\n' "$SERVICE_NAME"
printf '────────────────────────────────────────────\n'
printf '下一步：用 build_for_backend.sh 重新打包 APK，后端URL设为 https://%s\n' "$DEPLOY_DOMAIN"
