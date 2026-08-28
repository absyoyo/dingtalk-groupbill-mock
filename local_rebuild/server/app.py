from __future__ import annotations

import asyncio
import json
import os
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, ValidationError
from starlette.websockets import WebSocketDisconnect

from local_rebuild.server.device_crypto import DeviceKeyStore, SignVerifyError, decrypt_hybrid
from local_rebuild.server.event_hub import EventHub
from local_rebuild.server.event_log import EventLog


_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def _verify_api_key(header: str = Depends(_API_KEY_HEADER)) -> None:
    """Verify the X-API-Key header against the API_KEY environment variable.

    When ``API_KEY`` is unset/empty the check is a no-op (open mode).
    When set, requests without a matching ``X-API-Key`` header get
    HTTP 401 — applied to all ``/api/admin/*`` routes only.
    """
    expected = os.environ.get("API_KEY", "").strip()
    if not expected:
        return None
    if header is None or header.strip() != expected:
        raise HTTPException(status_code=401, detail="无效或缺失的 X-API-Key")
    return None


class UploadOrder(BaseModel):
    """Inbound payload for /api/device/upload_order."""

    user: str
    pay_order: str
    pay_id: str
    amount: float


class UploadSdk(BaseModel):
    """Inbound payload for /api/device/upload_sdk."""

    pay_id: str
    sdk_param: str


class MarkPaid(BaseModel):
    """Inbound payload for /api/device/mark_paid."""

    pay_id: str


class DebugEnvelope(BaseModel):
    """Envelope for /debug/ws/send (Task 4 placeholder).

    ``userId`` optionally routes the envelope to a single device;
    when omitted the envelope is broadcast to all registered devices.
    """

    type: str = Field(min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)
    userId: str | None = None


class AdminSend(BaseModel):
    """Envelope for /api/admin/send.

    ``userId`` optionally routes the envelope to a single device;
    when omitted it is broadcast to all registered devices.
    """

    type: str = Field(min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)
    userId: str | None = None


class CollectRequest(BaseModel):
    """Body for POST /api/admin/collect — trigger a pay-url fetch.

    ``groupBillId`` identifies the GroupBill to pay.  ``targetUid`` must
    equal the device's logged-in DingTalk uid (the APK drops mismatches).
    ``creatorUid`` is the bill creator; defaults to ``targetUid`` so a
    single-device self-test works out of the box.
    """

    groupBillId: str = Field(min_length=1)
    targetUid: str = Field(min_length=1)
    creatorUid: str | None = None
    timeoutSeconds: int = Field(default=30, ge=3, le=120)


@dataclass
class ActiveWebSocket:
    """Bookkeeping for one registered APK WebSocket."""

    websocket: WebSocket
    connection_id: str
    user_id: str = ""
    account_id: str = ""
    connected_at: float = 0.0
    last_ping_at: float = 0.0


class ConnectionManager:
    """Track APK WebSockets indexed by userId.

    Same-user reconnects replace the previous socket with close code 1001.
    Different users coexist. All state transitions are guarded by an
    app-scoped asyncio lock.
    """

    def __init__(self) -> None:
        self.devices: dict[str, ActiveWebSocket] = {}
        self._lock = asyncio.Lock()

    async def register(self, websocket: WebSocket, connection_id: str, user_id: str, account_id: str = "") -> None:
        """Associate *websocket* with *user_id* in the device map.

        If *user_id* already has a different registered socket, that old
        socket is closed with code 1001 (user-replaced) outside the lock
        so the old close never races with the new install.
        """
        record = ActiveWebSocket(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            account_id=account_id,
            connected_at=time.time(),
        )
        async with self._lock:
            old = self.devices.get(user_id)
            self.devices[user_id] = record
        if old is not None and old.websocket is not websocket:
            try:
                await old.websocket.close(code=1001, reason="user-replaced")
            except (WebSocketDisconnect, RuntimeError):
                pass

    async def disconnect(self, websocket: WebSocket) -> None:
        """Drop *websocket* from the device map when it is still registered."""
        async with self._lock:
            for user_id, record in list(self.devices.items()):
                if record.websocket is websocket:
                    del self.devices[user_id]

    async def send_to(self, user_id: str, envelope: dict[str, Any]) -> ActiveWebSocket | None:
        """Deliver *envelope* to the socket registered for *user_id*.

        Returns the delivered record, or ``None`` when the user has no
        registered device or the send fails.  A failed send clears the
        dead socket from the map.
        """
        async with self._lock:
            snapshot = self.devices.get(user_id)
        if snapshot is None:
            return None
        try:
            await snapshot.websocket.send_text(json.dumps(envelope))
        except (WebSocketDisconnect, RuntimeError):
            await self.disconnect(snapshot.websocket)
            return None
        return snapshot

    async def broadcast(self, envelope: dict[str, Any]) -> list[str]:
        """Deliver *envelope* to every registered device.

        Returns the list of userIds that received it; dead sockets are
        cleared from the map.
        """
        async with self._lock:
            snapshots = list(self.devices.values())
        delivered: list[str] = []
        for snapshot in snapshots:
            try:
                await snapshot.websocket.send_text(json.dumps(envelope))
                delivered.append(snapshot.user_id)
            except (WebSocketDisconnect, RuntimeError):
                await self.disconnect(snapshot.websocket)
        return delivered

    async def kick(self, user_id: str) -> bool:
        """Disconnect and drop the device registered for *user_id*.

        Returns ``True`` when a device was removed, ``False`` when the
        user had no registered device.
        """
        async with self._lock:
            record = self.devices.pop(user_id, None)
        if record is None:
            return False
        try:
            await record.websocket.close(code=1000, reason="kicked")
        except (WebSocketDisconnect, RuntimeError):
            pass
        return True

    def touch_ping(self, user_id: str) -> None:
        """Refresh the last-ping timestamp for the given user's device."""
        record = self.devices.get(user_id)
        if record is not None:
            record.last_ping_at = time.time()


def _normalize_body(value: Any) -> Any:
    """Return *value* with any inner bytes decoded as UTF-8.

    Top-level :class:`bytes` is decoded with ``errors='replace'``.
    :class:`str`, :class:`dict`, and :class:`list` pass through unchanged.
    """
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {_normalize_body(k): _normalize_body(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_body(i) for i in value]
    return value


def api_ok(data: Any = None, msg: str = "成功") -> dict[str, Any]:
    """Build a unified success response envelope."""
    return {"code": 0, "msg": msg, "data": data}


def api_fail(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    """Build a unified failure response envelope with a non-zero code."""
    return {"code": code, "msg": msg, "data": data}


CODE_INVALID_REQUEST = 1
CODE_UNSUPPORTED_TYPE = 2
CODE_NO_CLIENT = 3
CODE_UNKNOWN_USER = 4
CODE_COLLECT_TIMEOUT = 5


class CollectStore:
    """Correlate server-issued commands with their device replies.

    ``await_for`` parks on a per-key :class:`asyncio.Future` keyed by
    ``"{kind}:{group_bill_id}"`` (kind is ``pay``, ``detail`` or
    ``probe``) until an inbound ``alipay.upload`` (kind=pay) or
    ``rpc.result`` (kind=detail/probe) for the same bill arrives, or
    the timeout expires.
    """

    def __init__(self) -> None:
        self._waiters: dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def await_for(self, kind: str, group_bill_id: str, timeout: float) -> dict[str, Any] | None:
        """Wait up to *timeout* seconds for the bill's reply payload."""
        key = f"{kind}:{group_bill_id}"
        async with self._lock:
            future: asyncio.Future = asyncio.get_running_loop().create_future()
            self._waiters[key] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            async with self._lock:
                self._waiters.pop(key, None)

    def resolve(self, kind: str, group_bill_id: str, payload: dict[str, Any]) -> bool:
        """Complete the pending wait for *kind*+*group_bill_id* with *payload*."""
        future = self._waiters.get(f"{kind}:{group_bill_id}")
        if future is not None and not future.done():
            future.set_result(payload)
            return True
        return False


class DeviceRoleStore:
    """Persisted ``userId -> role`` bindings backed by a JSON file.

    Roles are ``master`` (商家/发起群收款的设备) or ``slave`` (子号/
    付款人设备,接收 bill.task 拉支付链接).  Bindings survive server
    restarts and are read on every ``GET /api/admin/devices`` call;
    unbound users fall back to auto-detection from event history.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._roles: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._load()

    def _load(self) -> None:
        """Read the JSON file if it exists; tolerate malformed content."""
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._roles = {str(k): str(v) for k, v in data.items()}
        except (OSError, json.JSONDecodeError):
            self._roles = {}

    async def set(self, user_id: str, role: str) -> None:
        """Bind *user_id* to *role* and persist to disk."""
        async with self._lock:
            self._roles[user_id] = role
            self._save()

    async def remove(self, user_id: str) -> bool:
        """Clear the binding for *user_id*; return True if it existed."""
        async with self._lock:
            existed = self._roles.pop(user_id, None) is not None
            if existed:
                self._save()
            return existed

    def get(self, user_id: str) -> str | None:
        """Return the bound role for *user_id*, or None when unbound."""
        return self._roles.get(user_id)

    def all(self) -> dict[str, str]:
        """Return a copy of all bindings."""
        return dict(self._roles)

    def _save(self) -> None:
        """Persist the bindings to the JSON file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._roles, ensure_ascii=False, indent=2), encoding="utf-8")


class LogcatCollector:
    """Stream ``adb logcat -s DtGroupBill:I`` lines into the event hub.

    Runs one daemon thread per application; ``adb`` failures disable the
    collector silently so the server still runs without a device.
    """

    def __init__(self, publish, log_path: Path) -> None:
        self._publish = publish
        self._log_path = log_path
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Spawn the collector thread once."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="logcat-collector", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the collector thread to exit."""
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                process = subprocess.Popen(
                    ["adb", "logcat", "-s", "DtGroupBill:I"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    errors="replace",
                )
            except (OSError, ValueError):
                return
            try:
                for line in process.stdout or []:
                    if self._stop.is_set():
                        break
                    self._emit(line.rstrip("\n"))
            finally:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
            if not self._stop.is_set():
                self._stop.wait(5)

    def _emit(self, line: str) -> None:
        if not line:
            return
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{time.time():.6f}\t{line}\n")
        self._publish({"source": "logcat", "level": "I", "tag": "DtGroupBill", "message": line})


def mount_console(app: FastAPI, static_root: Path) -> None:
    """Serve the built Vue console at / when the static build exists.

    Any previously mounted console at ``/`` (registered by an earlier
    ``create_app`` or a prior call) is replaced so the latest
    *static_root* wins.
    """
    if not static_root.exists():
        return
    app.router.routes[:] = [
        route for route in app.router.routes if getattr(route, "name", None) != "console"
    ]
    app.mount("/", StaticFiles(directory=static_root, html=True), name="console")


def create_app(event_log_path: str | Path) -> FastAPI:
    """Create an isolated GroupBill-compatible mock application.

    Parameters
    ----------
    event_log_path:
        Filesystem path for the JSONL event log file.

    Returns
    -------
    A fully-configured :class:`fastapi.FastAPI` instance with all HTTP
    routes, the validation error handler, and app-scoped state
    (:attr:`app.state.event_log` and :attr:`app.state.ws_manager`).
    """
    app = FastAPI(
        title="钉钉群账单 Mock 服务器 API",
        version="1.0.0",
        description=(
            "对外开放的 API 接口能力，分为以下分组：\n\n"
            "- **基础**: 健康检查\n"
            "- **设备上报**: APK 端 HTTP 上报订单/SDK/支付状态\n"
            "- **WebSocket**: APK 实时通信 + 控制台事件流\n"
            "- **设备管理**: 设备列表、角色绑定、踢下线\n"
            "- **账单中心**: bill.upsert 账单列表与聚合详情\n"
            "- **收款指令**: bill.task 下发等待 alipay.upload、rpc.call 详情/状态查询\n"
            "- **事件流**: 历史事件分页查询\n"
            "- **订单查询**: upload_order HTTP 上报记录\n"
            "- **日志**: 服务器日志 + 设备 logcat\n\n"
            "Swagger 文档: [/docs](/docs) | ReDoc: [/redoc](/redoc) | OpenAPI JSON: [/openapi.json](/openapi.json)\n\n"
            "若设置了环境变量 `API_KEY`，所有 `/api/admin/*` 接口需在请求头携带 `X-API-Key`。"
        ),
        openapi_tags=[
            {"name": "基础", "description": "健康检查"},
            {"name": "设备上报", "description": "APK 端 HTTP 上报（upload_order/upload_sdk/mark_paid）"},
            {"name": "WebSocket", "description": "APK 实时通信 + 控制台事件流订阅"},
            {"name": "设备管理", "description": "设备列表、角色绑定、踢下线"},
            {"name": "账单中心", "description": "bill.upsert 账单列表与聚合详情"},
            {"name": "收款指令", "description": "bill.task/rpc.call 下发与回调等待"},
            {"name": "事件流", "description": "历史事件分页查询"},
            {"name": "订单查询", "description": "upload_order HTTP 上报记录"},
            {"name": "日志", "description": "服务器日志 + 设备 logcat"},
        ],
    )
    app.state.event_log = EventLog(event_log_path)
    app.state.event_log_path = Path(event_log_path)
    app.state.ws_manager = ConnectionManager()
    app.state.event_hub = EventHub()
    app.state.collect_store = CollectStore()
    app.state.device_roles = DeviceRoleStore(app.state.event_log_path.parent / "device-roles.json")
    app.state.device_keys = DeviceKeyStore(app.state.event_log_path.parent / "device-keys.json")
    # 设备上报签名强制开关：1=未签名/验签失败一律 401；默认 log-only（照收并记录安全事件）
    app.state.device_sign_enforce = os.environ.get("DEVICE_SIGN_ENFORCE", "").strip() == "1"
    app.state.collect_logs_path = app.state.event_log_path.parent / "collect-logs.jsonl"
    logcat_log = app.state.event_log_path.parent / "device-logcat.log"
    app.state.logcat_log_path = logcat_log

    def publish_log(entry: dict[str, Any]) -> None:
        """Fan one structured log entry out to the admin event hub."""
        event = {
            "timestamp": time.time(),
            "connection_id": "logcat",
            "direction": "in",
            "transport": "logcat",
            "type": "device.log",
            "payload": entry,
        }
        app.state.event_hub.publish(event)

    app.state.logcat_collector = LogcatCollector(publish_log, logcat_log)
    if Path(app.state.event_log_path.parent / "logcat.enabled").exists():
        app.state.logcat_collector.start()

    def record(connection_id, direction, transport, event_type, payload):
        """Persist one event to the JSONL log and fan it out to the admin hub."""
        event = {
            "timestamp": time.time(),
            "connection_id": connection_id,
            "direction": direction,
            "transport": transport,
            "type": event_type,
            "payload": payload,
        }
        app.state.event_log.append_record(event)
        app.state.event_hub.publish(event)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        """Return and record a stable HTTP 400 response for malformed payloads."""
        connection_id = uuid.uuid4().hex
        payload: dict[str, Any] = {"rejected": True, "body": _normalize_body(error.body), "errors": error.errors()}
        record(connection_id, "in", "http", request.url.path, payload)
        response = api_fail(CODE_INVALID_REQUEST, "参数校验失败")
        record(connection_id, "out", "http", request.url.path, response)
        return JSONResponse(status_code=400, content=response)

    @app.get("/health", tags=["基础"], summary="健康检查", description="服务器存活探针。返回 `{code:0, data:{status:'ok'}}`。")
    async def health():
        """Report whether the local mock process is serving requests."""
        return api_ok(data={"status": "ok"})

    async def record_http(route: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist one inbound HTTP payload and its successful response."""
        connection_id = uuid.uuid4().hex
        record(connection_id, "in", "http", route, payload)
        response = api_ok()
        record(connection_id, "out", "http", route, response)
        return response

    async def _invalid_device_request(request: Request, errors: list[Any], body: Any = None) -> JSONResponse:
        """Record + return the same 400 shape as the RequestValidationError handler."""
        connection_id = uuid.uuid4().hex
        payload: dict[str, Any] = {"rejected": True, "body": _normalize_body(body), "errors": errors}
        record(connection_id, "in", "http", request.url.path, payload)
        response = api_fail(CODE_INVALID_REQUEST, "参数校验失败")
        record(connection_id, "out", "http", request.url.path, response)
        return JSONResponse(status_code=400, content=response)

    async def _read_device_payload(request: Request) -> tuple[dict[str, Any] | None, JSONResponse | None]:
        """Guard + parse one device report.

        * verifies ``X-Device-Id``/``X-Sign`` HMAC headers when present
          (``DEVICE_SIGN_ENFORCE=1`` rejects unsigned/invalid reports with 401;
          default log-only mode records a security event and proceeds)
        * transparently decrypts hybrid-wrapped bodies (``{"ek","iv","ct"}``)
        * returns ``(payload_dict, None)`` or ``(None, error_response)``
        """
        raw = await request.body()
        keys: DeviceKeyStore = app.state.device_keys
        device_id = request.headers.get("X-Device-Id") or ""
        signed = bool(device_id and request.headers.get("X-Sign"))
        if signed:
            try:
                keys.verify_headers(device_id, request.method, request.url.path, raw, dict(request.headers))
            except SignVerifyError as exc:
                record(uuid.uuid4().hex, "in", "http", request.url.path, {
                    "security": "device.sign_rejected", "device_id": device_id, "error": str(exc),
                })
                if app.state.device_sign_enforce:
                    return None, JSONResponse(
                        status_code=401,
                        content=api_fail(CODE_INVALID_REQUEST, f"设备签名校验失败: {exc}"),
                    )
        elif app.state.device_sign_enforce:
            return None, JSONResponse(
                status_code=401,
                content=api_fail(CODE_INVALID_REQUEST, "缺少设备签名（X-Device-Id/X-Sign）"),
            )

        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            return None, await _invalid_device_request(request, [{"type": "json_invalid", "msg": "invalid JSON"}], raw)
        if isinstance(parsed, dict) and set(parsed.keys()) == {"ek", "iv", "ct"}:
            priv_pem, _ = keys.server_keypair()
            try:
                decrypted = decrypt_hybrid(priv_pem, parsed)
            except SignVerifyError as exc:
                return None, await _invalid_device_request(request, [{"type": "decrypt", "msg": str(exc)}], parsed)
            try:
                parsed = json.loads(decrypted)
            except json.JSONDecodeError:
                return None, await _invalid_device_request(request, [{"type": "json_invalid", "msg": "decrypted payload is not JSON"}], decrypted)
        if not isinstance(parsed, dict):
            return None, await _invalid_device_request(request, [{"type": "model", "msg": "body must be a JSON object"}], parsed)
        return parsed, None

    @app.post("/api/device/enroll", tags=["设备上报"], summary="设备密钥注册", description="设备生成本机 RSA 密钥对后注册：服务器签发 device_id，并用设备公钥 RSA-OAEP 加密下发 HMAC 签名密钥。")
    async def device_enroll(request: Request):
        """Issue per-device signing credentials (secret encrypted to the device key)."""
        raw = await request.body()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            return await _invalid_device_request(request, [{"type": "json_invalid", "msg": "invalid JSON"}], raw)
        if not isinstance(payload, dict):
            return await _invalid_device_request(request, [{"type": "model", "msg": "body must be a JSON object"}], payload)
        user_id = str(payload.get("userId") or "")
        account_id = str(payload.get("accountId") or "")
        device_public_key = str(payload.get("devicePublicKey") or "")
        if not user_id or not device_public_key:
            return await _invalid_device_request(request, [{"type": "missing", "msg": "userId/devicePublicKey required"}], payload)
        try:
            result = app.state.device_keys.enroll(user_id, account_id, device_public_key)
        except SignVerifyError as exc:
            return await _invalid_device_request(request, [{"type": "enroll", "msg": str(exc)}], payload)
        connection_id = uuid.uuid4().hex
        record(connection_id, "in", "http", "/api/device/enroll", {"userId": user_id, "accountId": account_id})
        response = api_ok(data=result)
        record(connection_id, "out", "http", "/api/device/enroll", response)
        return response

    @app.post("/api/device/upload_order", tags=["设备上报"], summary="上报订单", description="APK 端发起群收款时上报订单信息：user/pay_order/pay_id/amount。支持 HMAC 签名头与混合加密体。")
    async def upload_order(request: Request):
        """Receive the injected module's order metadata report."""
        payload, err = await _read_device_payload(request)
        if err is not None:
            return err
        try:
            model = UploadOrder(**payload)
        except ValidationError as exc:
            return await _invalid_device_request(request, exc.errors(), payload)
        return await record_http("/api/device/upload_order", model.model_dump())

    @app.post("/api/device/upload_sdk", tags=["设备上报"], summary="上报SDK参数", description="APK 端调起支付SDK时上报：pay_id/sdk_param。支持 HMAC 签名头与混合加密体。")
    async def upload_sdk(request: Request):
        """Receive the injected module's payment SDK parameter report."""
        payload, err = await _read_device_payload(request)
        if err is not None:
            return err
        try:
            model = UploadSdk(**payload)
        except ValidationError as exc:
            return await _invalid_device_request(request, exc.errors(), payload)
        return await record_http("/api/device/upload_sdk", model.model_dump())

    @app.post("/api/device/mark_paid", tags=["设备上报"], summary="标记已支付", description="APK 端支付成功后上报：pay_id。支持 HMAC 签名头与混合加密体。")
    async def mark_paid(request: Request):
        """Receive a local paid-state notification for a payment ID."""
        payload, err = await _read_device_payload(request)
        if err is not None:
            return err
        try:
            model = MarkPaid(**payload)
        except ValidationError as exc:
            return await _invalid_device_request(request, exc.errors(), payload)
        return await record_http("/api/device/mark_paid", model.model_dump())

    @app.websocket("/ws", name="apk_ws")
    async def ws_endpoint(ws: WebSocket):
        """WebSocket endpoint for APK real-time communication.

        Accepts JSON envelopes with ``type`` and ``data`` fields.
        A ``register`` envelope binds this socket to its ``userId``
        (replacing any previous socket for the same user) and responds
        with an ``ack`` containing ``registered``, the echoed ``userId``,
        and ``pendingTasks: 0``.  A ``ping`` is echoed back as ``pong``
        with identical ``data`` and refreshes the device's ping timestamp.
        All valid inbound envelopes are logged.  Malformed JSON yields
        a ``parse_error`` error envelope; missing ``type`` yields a
        ``protocol_error`` error envelope.
        """
        await ws.accept()
        manager: ConnectionManager = app.state.ws_manager
        connection_id = uuid.uuid4().hex

        try:
            record(connection_id, "in", "ws", "connected", {})
            ws_user_id = ""
            while True:
                text = await ws.receive_text()
                try:
                    envelope = json.loads(text)
                except (json.JSONDecodeError, TypeError):
                    record(connection_id, "in", "ws", "parse_error", {})
                    await ws.send_text(json.dumps({"type": "error", "data": {"message": "parse_error"}}))
                    continue

                if not isinstance(envelope, dict) or "type" not in envelope:
                    record(connection_id, "in", "ws", "protocol_error", {})
                    await ws.send_text(json.dumps({"type": "error", "data": {"message": "protocol_error"}}))
                    continue

                msg_type: str = envelope["type"]
                record(connection_id, "in", "ws", msg_type, envelope)

                # 设备 WS envelope 验签（log-only）：data.sig 存在时校验，
                # 失败记录安全事件后仍按原流程处理（enforce 开关不作用于 WS）
                if msg_type in ("bill.upsert", "alipay.upload", "rpc.result") and ws_user_id:
                    data_ws = envelope.get("data")
                    if isinstance(data_ws, dict) and data_ws.get("sig"):
                        device_rec = app.state.device_keys.device_id_for_user(ws_user_id)
                        if device_rec:
                            try:
                                app.state.device_keys.verify_ws_envelope(device_rec, envelope)
                            except SignVerifyError as exc:
                                record(connection_id, "in", "ws", "security.ws_sign_rejected", {
                                    "user_id": ws_user_id, "error": str(exc),
                                })

                if msg_type == "alipay.upload":
                    data = envelope.get("data", {}) if isinstance(envelope.get("data"), dict) else {}
                    bill_id = data.get("groupBillId", "")
                    if bill_id:
                        app.state.collect_store.resolve("pay", bill_id, data)
                elif msg_type == "rpc.result":
                    data = envelope.get("data", {}) if isinstance(envelope.get("data"), dict) else {}
                    bill_id = data.get("groupBillId", "")
                    if bill_id:
                        for kind in ("detail", "probe"):
                            app.state.collect_store.resolve(kind, bill_id, data)

                if msg_type == "register":
                    data = envelope.get("data", {})
                    user_id: str = data.get("userId", "") if isinstance(data, dict) else ""
                    account_id: str = data.get("accountId", "") if isinstance(data, dict) else ""
                    ws_user_id = user_id
                    await manager.register(ws, connection_id, user_id, account_id)
                    ack = {
                        "type": "ack",
                        "data": {"message": "registered", "userId": user_id, "pendingTasks": 0},
                    }
                    await ws.send_text(json.dumps(ack))
                    record(connection_id, "out", "ws", "ack", ack)
                elif msg_type == "ping":
                    ping_data = envelope.get("data", {})
                    if isinstance(ping_data, dict) and ping_data.get("userId"):
                        manager.touch_ping(ping_data["userId"])
                    pong = {"type": "pong", "data": envelope.get("data", "")}
                    await ws.send_text(json.dumps(pong))
                    record(connection_id, "out", "ws", "pong", pong)
        except WebSocketDisconnect:
            pass
        except RuntimeError:
            record(connection_id, "in", "ws", "socket_error", {})
        finally:
            record(connection_id, "in", "ws", "disconnected", {})
            await manager.disconnect(ws)
            try:
                await ws.close(code=1011, reason="socket-error")
            except (WebSocketDisconnect, RuntimeError):
                pass

    @app.websocket("/api/admin/ws", name="admin_ws")
    async def admin_ws(ws: WebSocket):
        """Live event stream for the console UI."""
        await ws.accept()
        queue = app.state.event_hub.subscribe()
        try:
            while True:
                event = await queue.get()
                await ws.send_text(json.dumps(event))
        except WebSocketDisconnect:
            pass
        finally:
            app.state.event_hub.unsubscribe(queue)

    _ALLOWED_DEBUG_TYPES: set[str] = {"bill.task", "orders.follow", "bill.done", "rpc.call", "alipay.result"}

    @app.post("/debug/ws/send", tags=["收款指令"], summary="调试-下发消息", description="直接给 APK WebSocket 发送 allowlist 消息（不等待回调）。", dependencies=[Depends(_verify_api_key)])
    async def debug_ws_send(body: DebugEnvelope):
        """Deliver an envelope to one APK WebSocket or broadcast it.

        A ``userId`` in the body routes the envelope to that user's
        device (HTTP 409 when the user has no registered device).
        Without ``userId`` the envelope is broadcast to every registered
        device (HTTP 409 when no device is connected).  Only allowlisted
        message types are accepted (HTTP 400 otherwise).
        """
        manager: ConnectionManager = app.state.ws_manager

        if body.type not in _ALLOWED_DEBUG_TYPES:
            return JSONResponse(status_code=400, content=api_fail(CODE_UNSUPPORTED_TYPE, "不支持的消息类型"))

        envelope = body.model_dump(exclude={"userId"})
        if body.userId is not None:
            result = await manager.send_to(body.userId, envelope)
            if result is None:
                return JSONResponse(status_code=409, content=api_fail(CODE_NO_CLIENT, "设备未连接"))
            record(result.connection_id, "out", "ws", body.type, envelope)
            return api_ok()

        delivered = await manager.broadcast(envelope)
        if not delivered:
            return JSONResponse(status_code=409, content=api_fail(CODE_NO_CLIENT, "设备未连接"))
        for user_id in delivered:
            device = manager.devices.get(user_id)
            if device is not None:
                record(device.connection_id, "out", "ws", body.type, envelope)
        return api_ok(data={"delivered": delivered})

    @app.get("/api/admin/devices", tags=["设备管理"], summary="设备列表+角色", description="返回所有在线 APK 设备，含 role（master/slave/unknown）和 roleSource（bound/auto）。", dependencies=[Depends(_verify_api_key)])
    async def admin_devices():
        """List all registered APK devices with connection metadata + role.

        Role resolution precedence:
        1. ``device-roles.json`` manual binding (highest priority)
        2. Auto-detection from event history
           - ``master`` if the user ever sent a ``bill.upsert``
           - ``slave`` if the user was ever a ``bill.task`` targetUid
        3. ``unknown`` when neither source has data
        """
        manager: ConnectionManager = app.state.ws_manager
        role_store: DeviceRoleStore = app.state.device_roles
        history = _load_history()
        upsert_uids = {
            e.get("payload", {}).get("data", {}).get("currentUid", "")
            for e in history
            if e["direction"] == "in" and e["type"] == "bill.upsert"
        }
        target_uids = set()
        for e in history:
            if e["direction"] != "out" or e["type"] != "bill.task":
                continue
            target_uids.add(e.get("payload", {}).get("data", {}).get("targetUid", ""))
        devices = []
        for record in manager.devices.values():
            bound = role_store.get(record.user_id)
            if bound:
                role = bound
                role_source = "bound"
            elif record.user_id in upsert_uids:
                role = "master"
                role_source = "auto"
            elif record.user_id in target_uids:
                role = "slave"
                role_source = "auto"
            else:
                role = "unknown"
                role_source = "auto"
            devices.append({
                "userId": record.user_id,
                "accountId": record.account_id,
                "connectionId": record.connection_id,
                "connectedAt": record.connected_at,
                "lastPingAt": record.last_ping_at,
                "role": role,
                "roleSource": role_source,
            })
        return api_ok(data={"devices": devices, "bindings": role_store.all()})

    def _load_history() -> list[dict]:
        """Read every recorded event from the JSONL log, oldest first."""
        path = Path(app.state.event_log_path)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def _extract_bill_id(data: dict[str, Any]) -> str:
        """Pull a groupBillId out of a bill.upsert payload if not top-level."""
        model = data.get("groupBillModel") if isinstance(data.get("groupBillModel"), dict) else {}
        if isinstance(model, dict):
            bid = model.get("groupBillId") or model.get("id")
            if bid:
                return str(bid)
        items = data.get("groupBillItem")
        if isinstance(items, list) and items:
            first = items[0] if isinstance(items[0], dict) else {}
            bid = first.get("groupBillId") or first.get("billId")
            if bid:
                return str(bid)
        return ""

    def _bill_matches(event: dict[str, Any], group_bill_id: str) -> bool:
        """True if *event* carries *group_bill_id* anywhere in its payload."""
        def _scan(obj: Any) -> bool:
            if isinstance(obj, str):
                return obj == group_bill_id
            if isinstance(obj, dict):
                return any(_scan(v) for v in obj.values())
            if isinstance(obj, list):
                return any(_scan(v) for v in obj)
            return False
        return _scan(event.get("payload", {}))

    async def _dispatch_rpc_call(app_obj: FastAPI, body: CollectRequest, kind: str, uri: str) -> JSONResponse:
        """Send rpc.call envelope and await rpc.result for *kind*/*groupBillId*."""
        manager: ConnectionManager = app_obj.state.ws_manager
        if body.targetUid not in manager.devices:
            return JSONResponse(status_code=409, content=api_fail(CODE_NO_CLIENT, "设备未连接"))
        creator = body.creatorUid or body.targetUid
        envelope = {
            "type": "rpc.call",
            "data": {
                "method": kind,
                "uri": uri,
                "groupBillId": body.groupBillId,
                "creatorUid": creator,
                "targetUid": body.targetUid,
                "requestId": uuid.uuid4().hex,
            },
        }
        wait_task = asyncio.create_task(
            app_obj.state.collect_store.await_for(kind, body.groupBillId, float(body.timeoutSeconds))
        )
        snapshot = await manager.send_to(body.targetUid, envelope)
        if snapshot is None:
            wait_task.cancel()
            return JSONResponse(status_code=409, content=api_fail(CODE_NO_CLIENT, "设备未连接"))
        record(snapshot.connection_id, "out", "ws", "rpc.call", envelope)
        result = await wait_task
        if result is None:
            return JSONResponse(
                status_code=504,
                content=api_fail(CODE_COLLECT_TIMEOUT, f"等待 {kind} 响应超时（{body.timeoutSeconds}s）"),
            )
        if "error" in result:
            return JSONResponse(status_code=502, content=api_fail(CODE_COLLECT_TIMEOUT, f"设备端返回错误: {result['error']}"))
        return api_ok(data=result)

    @app.get("/api/admin/events", tags=["事件流"], summary="事件历史", description="分页查询所有事件（bill.upsert/alipay.upload/rpc.result 等），支持 type/transport/direction 过滤。", dependencies=[Depends(_verify_api_key)])
    async def admin_events(type: str | None = None, transport: str | None = None, direction: str | None = None, page: int = 1, size: int = 50):
        """Return paginated event history with optional type/transport/direction filters."""
        history = _load_history()
        filtered = [
            event for event in history
            if (type is None or event["type"] == type)
            and (transport is None or event["transport"] == transport)
            and (direction is None or event["direction"] == direction)
        ]
        filtered.reverse()
        start = (page - 1) * size
        return api_ok(data={"total": len(filtered), "items": filtered[start : start + size]})

    @app.get("/api/admin/orders", tags=["订单查询"], summary="订单上报记录", description="分页查询 upload_order HTTP 上报记录（user/pay_order/pay_id/amount）。", dependencies=[Depends(_verify_api_key)])
    async def admin_orders(page: int = 1, size: int = 20):
        """Return paginated inbound upload_order records from the event log."""
        history = _load_history()
        orders = [event for event in history if event["type"] == "/api/device/upload_order" and event["direction"] == "in"]
        orders.reverse()
        start = (page - 1) * size
        return api_ok(data={"total": len(orders), "items": orders[start : start + size]})

    @app.post("/api/admin/send", tags=["收款指令"], summary="通用消息下发", description="下发 allowlist 消息到指定 userId 或广播，不等回调。", dependencies=[Depends(_verify_api_key)])
    async def admin_send(body: AdminSend):
        """Deliver an allowlisted envelope to one APK device or broadcast it."""
        if body.type not in _ALLOWED_DEBUG_TYPES:
            return JSONResponse(status_code=400, content=api_fail(CODE_UNSUPPORTED_TYPE, "不支持的消息类型"))
        envelope = {"type": body.type, "data": body.data}
        if body.userId is None:
            delivered = await app.state.ws_manager.broadcast(envelope)
            if not delivered:
                return JSONResponse(status_code=409, content=api_fail(CODE_NO_CLIENT, "设备未连接"))
            for user_id in delivered:
                record(connection_id := f"admin:{user_id}", "out", "ws", body.type, envelope)
            return api_ok(data={"delivered": delivered})
        snapshot = await app.state.ws_manager.send_to(body.userId, envelope)
        if snapshot is None:
            return JSONResponse(status_code=409, content=api_fail(CODE_NO_CLIENT, "设备未连接"))
        record(snapshot.connection_id, "out", "ws", body.type, envelope)
        return api_ok(data={"delivered": [body.userId]})

    @app.post("/api/admin/collect", tags=["收款指令"], summary="拉支付链接", description="下发 bill.task 给子号，等待 alipay.upload 回调返回 payUrl 支付串。超时返回 504。", dependencies=[Depends(_verify_api_key)])
    async def admin_collect(body: CollectRequest):
        """Dispatch a bill.task and await the device's alipay.upload reply.

        Sends ``bill.task`` with the caller-supplied ``groupBillId`` /
        ``creatorUid`` / ``targetUid`` triple to the device registered
        for ``targetUid`` (HTTP 409 when absent), then parks on the
        collect store until the APK's ``alipay.upload`` (payUrl) or an
        ``rpc.result`` error for the same bill arrives.  Times out with
        ``code`` 5 after ``timeoutSeconds``.
        """
        manager: ConnectionManager = app.state.ws_manager
        if body.targetUid not in manager.devices:
            return JSONResponse(status_code=409, content=api_fail(CODE_NO_CLIENT, "设备未连接"))

        creator = body.creatorUid or body.targetUid
        envelope = {
            "type": "bill.task",
            "data": {
                "groupBillId": body.groupBillId,
                "creatorUid": creator,
                "targetUid": body.targetUid,
            },
        }
        wait_task = asyncio.create_task(
            app.state.collect_store.await_for("pay", body.groupBillId, float(body.timeoutSeconds))
        )
        snapshot = await manager.send_to(body.targetUid, envelope)
        if snapshot is None:
            wait_task.cancel()
            return JSONResponse(status_code=409, content=api_fail(CODE_NO_CLIENT, "设备未连接"))
        record(snapshot.connection_id, "out", "ws", "bill.task", envelope)

        result = await wait_task
        if result is None:
            return JSONResponse(
                status_code=504,
                content=api_fail(
                    CODE_COLLECT_TIMEOUT,
                    f"等待支付链接超时（{body.timeoutSeconds}s）— 请查看日志定位设备端卡点",
                ),
            )
        if "error" in result:
            return JSONResponse(
                status_code=502,
                content=api_fail(CODE_COLLECT_TIMEOUT, f"设备端返回错误: {result['error']}"),
            )
        return api_ok(data=result)

    @app.get("/api/admin/bills", tags=["账单中心"], summary="账单列表", description="从 bill.upsert 提取所有账单，含状态聚合（pending/link_fetched/paid）。", dependencies=[Depends(_verify_api_key)])
    async def admin_bills(page: int = 1, size: int = 20):
        """Return paginated GroupBill records aggregated from bill.upsert events.

        Each row carries the bill's creator/amount/items from its
        ``bill.upsert`` payload plus a ``status`` field aggregated from
        later ``alipay.upload`` and ``mark_paid`` events for the same
        ``groupBillId``: ``pending`` (no payUrl yet), ``link_fetched``
        (alipay.upload seen), ``paid`` (mark_paid seen).
        """
        history = _load_history()
        bills: list[dict[str, Any]] = []
        seen: set[str] = set()
        pay_url_seen: set[str] = set()
        paid_seen: set[str] = set()
        for event in history:
            if event["direction"] != "in":
                continue
            if event["type"] == "alipay.upload":
                bid = event.get("payload", {}).get("data", {}).get("groupBillId", "")
                if bid:
                    pay_url_seen.add(bid)
            elif event["type"] == "/api/device/mark_paid":
                pay_id = event.get("payload", {}).get("pay_id", "")
                paid_seen.add(pay_id)
        for event in history:
            if event["direction"] != "in" or event["type"] != "bill.upsert":
                continue
            data = event.get("payload", {}).get("data", {})
            bid = data.get("groupBillId") or _extract_bill_id(data)
            if not bid or bid in seen:
                continue
            seen.add(bid)
            # pay_id 格式为 "{groupBillId}_{payerUid}"，以账单 ID 开头
            status = "paid" if bid in paid_seen or any(p.startswith(bid + "_") for p in paid_seen) else (
                "link_fetched" if bid in pay_url_seen else "pending"
            )
            bills.append({
                "groupBillId": bid,
                "creatorUid": data.get("creatorUid", data.get("currentUid", "")),
                "accountId": data.get("accountId", ""),
                "createSource": data.get("createSource", ""),
                "groupBillModel": data.get("groupBillModel", {}),
                "groupBillItem": data.get("groupBillItem", []),
                "timestamp": event.get("timestamp", 0),
                "status": status,
            })
        bills.sort(key=lambda b: b["timestamp"], reverse=True)
        total = len(bills)
        start = (page - 1) * size
        return api_ok(data={"total": total, "items": bills[start : start + size]})

    @app.get("/api/admin/bills/{group_bill_id}", tags=["账单中心"], summary="账单聚合详情", description="返回单笔账单的所有关联事件（bill.upsert+alipay.upload+mark_paid+rpc.result）。", dependencies=[Depends(_verify_api_key)])
    async def admin_bill_detail(group_bill_id: str):
        """Return one GroupBill with all related events aggregated."""
        history = _load_history()
        related: list[dict[str, Any]] = []
        upsert = None
        for event in history:
            data = event.get("payload", {}).get("data", event.get("payload", {}))
            bid = data.get("groupBillId") if isinstance(data, dict) else ""
            is_mark_paid = (
                event["type"] == "/api/device/mark_paid"
                and event.get("payload", {}).get("pay_id", "").startswith(f"{group_bill_id}_")
            )
            if bid != group_bill_id and not _bill_matches(event, group_bill_id) and not is_mark_paid:
                continue
            related.append(event)
            if event["type"] == "bill.upsert" and event["direction"] == "in" and upsert is None:
                upsert = data
        return api_ok(data={"groupBillId": group_bill_id, "upsert": upsert, "events": related})

    @app.post("/api/admin/query-detail", tags=["收款指令"], summary="查账单详情", description="下发 rpc.call {method:detail} 给子号，等待 rpc.result 返回 queryGroupBillDetail 结果。", dependencies=[Depends(_verify_api_key)])
    async def admin_query_detail(body: CollectRequest):
        """Dispatch rpc.call {method: detail} and await rpc.result reply."""
        return await _dispatch_rpc_call(app, body, "detail", "queryGroupBillDetail")

    @app.post("/api/admin/query-pay-status", tags=["收款指令"], summary="查支付状态", description="下发 rpc.call {method:probePayStatus} 给子号，等待 rpc.result 返回 syncGroupBillPayStatusV2 结果。", dependencies=[Depends(_verify_api_key)])
    async def admin_query_pay_status(body: CollectRequest):
        """Dispatch rpc.call {method: probe.payStatus} and await rpc.result."""
        return await _dispatch_rpc_call(app, body, "probe", "syncGroupBillPayStatusV2")

    @app.get("/api/admin/logs", tags=["日志"], summary="服务器日志", description="分页查询 uvicorn stdout 日志，支持 level/keyword 过滤。", dependencies=[Depends(_verify_api_key)])
    async def admin_logs(level: str | None = None, keyword: str | None = None, page: int = 1, size: int = 100):
        """Return paginated server stdout log lines with optional filters."""
        log_path = app.state.event_log_path.parent / "mock-server.stdout.log"
        if not log_path.exists():
            return api_ok(data={"total": 0, "items": []})
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if keyword:
            lines = [ln for ln in lines if keyword in ln]
        if level:
            lines = [ln for ln in lines if f"| {level.upper()}" in ln or level.upper() in ln]
        lines.reverse()
        start = (page - 1) * size
        return api_ok(data={"total": len(lines), "items": lines[start : start + size]})

    @app.get("/api/admin/logcat", tags=["日志"], summary="设备logcat", description="分页查询手机 DtGroupBill logcat（需先 toggle 启动采集）。", dependencies=[Depends(_verify_api_key)])
    async def admin_logcat(keyword: str | None = None, page: int = 1, size: int = 100):
        """Return paginated device logcat lines captured from DtGroupBill."""
        log_path: Path = app.state.logcat_log_path
        if not log_path.exists():
            return api_ok(data={"total": 0, "items": []})
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if keyword:
            lines = [ln for ln in lines if keyword in ln]
        lines.reverse()
        start = (page - 1) * size
        return api_ok(data={"total": len(lines), "items": lines[start : start + size]})

    @app.post("/api/admin/logcat/toggle", tags=["日志"], summary="启停logcat采集", description="启动/停止 adb logcat -s DtGroupBill:I 后台采集，状态写入 logcat.enabled 标记文件。", dependencies=[Depends(_verify_api_key)])
    async def admin_logcat_toggle():
        """Start or stop the adb logcat collector and report the new state."""
        collector: LogcatCollector = app.state.logcat_collector
        flag = app.state.event_log_path.parent / "logcat.enabled"
        if collector._thread is not None and not collector._stop.is_set():
            collector.stop()
            flag.unlink(missing_ok=True)
            state = "stopped"
        else:
            app.state.logcat_collector = LogcatCollector(publish_log, app.state.logcat_log_path)
            app.state.logcat_collector.start()
            flag.write_text("1", encoding="utf-8")
            state = "running"
        return api_ok(data={"state": state})

    @app.post("/api/admin/devices/{user_id}/role", tags=["设备管理"], summary="绑定设备角色", description="把 userId 绑定为主号(master)或子号(slave)，持久化到 device-roles.json。传 role=clear 解绑。", dependencies=[Depends(_verify_api_key)])
    async def admin_set_role(user_id: str, body: dict[str, Any]):
        """Bind *user_id* to a role (``master``/``slave``) persistently.

        Body: ``{"role": "master"}`` or ``{"role": "slave"}``.  Pass an
        empty ``role`` (or ``"unknown"``) to clear the binding.
        """
        role = str(body.get("role", "")).strip().lower()
        role_store: DeviceRoleStore = app.state.device_roles
        if role in ("", "unknown", "auto", "clear", "remove"):
            removed = await role_store.remove(user_id)
            return api_ok(data={"userId": user_id, "role": None, "cleared": removed})
        if role not in ("master", "slave"):
            return JSONResponse(
                status_code=400,
                content=api_fail(CODE_INVALID_REQUEST, "role 必须是 master 或 slave"),
            )
        await role_store.set(user_id, role)
        return api_ok(data={"userId": user_id, "role": role, "bound": True})

    @app.delete("/api/admin/devices/{user_id}", tags=["设备管理"], summary="踢设备下线", description="断开 userId 对应的 WebSocket 连接（close code 1000）。", dependencies=[Depends(_verify_api_key)])
    async def admin_kick(user_id: str):
        """Disconnect and drop the device registered for *user_id*."""
        kicked = await app.state.ws_manager.kick(user_id)
        if not kicked:
            return JSONResponse(status_code=404, content=api_fail(CODE_UNKNOWN_USER, "用户不存在"))
        return api_ok()

    static_root = Path(__file__).resolve().parent / "static"
    mount_console(app, static_root)

    return app
