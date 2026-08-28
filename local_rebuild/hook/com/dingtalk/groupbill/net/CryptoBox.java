package com.dingtalk.groupbill.net;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.MessageDigest;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.SecureRandom;
import java.security.spec.MGF1ParameterSpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.UUID;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.Mac;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.OAEPParameterSpec;
import javax.crypto.spec.PSource;
import javax.crypto.spec.SecretKeySpec;
import org.json.JSONObject;

/**
 * Device-side crypto for the APK&lt;-&gt;server protocol.
 *
 * Enrollment: generate a device RSA-2048 keypair, POST the public key to
 * {@code /api/device/enroll}, RSA-OAEP-decrypt the HMAC secret the server
 * issues. Subsequent HTTP reports are AES-256-GCM encrypted (key wrapped
 * with the server RSA public key) and HMAC-SHA256 signed. WS envelopes
 * for payment-related types get {@code ts}/{@code nonce}/{@code sig}.
 *
 * Failures are swallowed so a crypto error never blocks the original
 * report path (server log-only mode still accepts unsigned traffic).
 */
public final class CryptoBox {
    private static final OAEPParameterSpec OAEP = new OAEPParameterSpec(
            "SHA-256", "MGF1", MGF1ParameterSpec.SHA256, PSource.PSpecified.DEFAULT);
    private static final Object LOCK = new Object();
    private static String userId = "";
    private static String accountId = "";
    private static String deviceId = "";
    private static byte[] hmacSecret;
    private static PublicKey serverPublicKey;
    private static PrivateKey devicePrivateKey;
    private static boolean enrolled;

    private CryptoBox() {}

    public static void setIdentity(String uid, String aid) {
        if (uid == null || uid.isEmpty()) {
            return;
        }
        synchronized (LOCK) {
            if (!uid.equals(userId)) {
                enrolled = false;
            }
            userId = uid;
            accountId = aid == null ? "" : aid;
        }
    }

    public static void ensureEnrolled() {
        synchronized (LOCK) {
            if (enrolled || userId.isEmpty()) {
                return;
            }
            try {
                doEnrollLocked();
            } catch (Throwable t) {
                try {
                    Class.forName("com.dingtalk.groupbill.util.DtLog")
                            .getMethod("e", String.class, Throwable.class)
                            .invoke(null, "CryptoBox enroll FAILED", t);
                } catch (Throwable ignored) {
                    // logging is best-effort
                }
            }
        }
    }

    /**
     * Wrap {@code plain} as hybrid ciphertext and attach HMAC signature
     * headers on {@code conn}. Returns the bytes to write. On any failure
     * returns the original UTF-8 JSON (unsigned fallback).
     */
    public static byte[] prepareHttp(HttpURLConnection conn, String path, JSONObject plain) {
        byte[] original = plain.toString().getBytes(StandardCharsets.UTF_8);
        try {
            ensureEnrolled();
            synchronized (LOCK) {
                if (!enrolled || hmacSecret == null || serverPublicKey == null) {
                    return original;
                }
            }
            JSONObject wrapped = encryptHybrid(plain.toString().getBytes(StandardCharsets.UTF_8));
            byte[] body = wrapped.toString().getBytes(StandardCharsets.UTF_8);
            applySignHeaders(conn, "POST", path, body);
            return body;
        } catch (Throwable t) {
            return original;
        }
    }

    /** Add {@code ts}/{@code nonce}/{@code sig} onto payment-related WS data. */
    public static void signWsData(String type, JSONObject data) {
        if (data == null || type == null) {
            return;
        }
        if (!"bill.upsert".equals(type) && !"alipay.upload".equals(type) && !"rpc.result".equals(type)) {
            return;
        }
        try {
            ensureEnrolled();
            byte[] secret;
            synchronized (LOCK) {
                if (!enrolled || hmacSecret == null) {
                    return;
                }
                secret = hmacSecret;
            }
            long ts = System.currentTimeMillis() / 1000L;
            String nonce = UUID.randomUUID().toString().replace("-", "");
            data.put("ts", ts);
            data.put("nonce", nonce);
            // Must match server: json.dumps({k:v for k,v in data.items() if k!="sig"}, sort_keys=True, separators=(",",":"))
            String canonical = sortedJson(data);
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret, "HmacSHA256"));
            data.put("sig", toHex(mac.doFinal(canonical.getBytes(StandardCharsets.UTF_8))));
        } catch (Throwable ignored) {
            // unsigned fallback
        }
    }

    private static void doEnrollLocked() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048, new SecureRandom());
        KeyPair pair = kpg.generateKeyPair();
        devicePrivateKey = pair.getPrivate();
        String pubPem = toPem("PUBLIC KEY", pair.getPublic().getEncoded());

        JSONObject req = new JSONObject();
        req.put("userId", userId);
        req.put("accountId", accountId);
        req.put("devicePublicKey", pubPem);
        String respText = httpPost("/api/device/enroll", req.toString());
        JSONObject resp = new JSONObject(respText);
        if (resp.optInt("code", -1) != 0) {
            throw new IllegalStateException("enroll code=" + resp.optInt("code"));
        }
        JSONObject data = resp.getJSONObject("data");
        deviceId = data.getString("device_id");
        String encB64 = data.getString("enc_hmac_secret");
        String serverPem = data.getString("server_public_key");

        Cipher rsa = Cipher.getInstance("RSA/ECB/OAEPPadding");
        rsa.init(Cipher.DECRYPT_MODE, devicePrivateKey, OAEP);
        hmacSecret = rsa.doFinal(fromB64(encB64));
        serverPublicKey = KeyFactory.getInstance("RSA").generatePublic(
                new X509EncodedKeySpec(fromPem(serverPem)));
        enrolled = true;
    }

    private static JSONObject encryptHybrid(byte[] payload) throws Exception {
        KeyGenerator kg = KeyGenerator.getInstance("AES");
        kg.init(256, new SecureRandom());
        SecretKey aes = kg.generateKey();
        byte[] iv = new byte[12];
        new SecureRandom().nextBytes(iv);
        Cipher gcm = Cipher.getInstance("AES/GCM/NoPadding");
        gcm.init(Cipher.ENCRYPT_MODE, aes, new GCMParameterSpec(128, iv));
        byte[] ct = gcm.doFinal(payload);

        Cipher rsa = Cipher.getInstance("RSA/ECB/OAEPPadding");
        rsa.init(Cipher.ENCRYPT_MODE, serverPublicKey, OAEP);
        byte[] ek = rsa.doFinal(aes.getEncoded());

        JSONObject out = new JSONObject();
        out.put("ek", toB64(ek));
        out.put("iv", toB64(iv));
        out.put("ct", toB64(ct));
        return out;
    }

    private static void applySignHeaders(HttpURLConnection conn, String method, String path, byte[] body)
            throws Exception {
        long ts = System.currentTimeMillis() / 1000L;
        String nonce = UUID.randomUUID().toString().replace("-", "");
        MessageDigest sha = MessageDigest.getInstance("SHA-256");
        String bodyHex = toHex(sha.digest(body));
        String canonical = method.toUpperCase() + "\n" + path + "\n" + ts + "\n" + nonce + "\n" + bodyHex;
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(hmacSecret, "HmacSHA256"));
        String sign = toHex(mac.doFinal(canonical.getBytes(StandardCharsets.UTF_8)));
        conn.setRequestProperty("X-Device-Id", deviceId);
        conn.setRequestProperty("X-Timestamp", String.valueOf(ts));
        conn.setRequestProperty("X-Nonce", nonce);
        conn.setRequestProperty("X-Sign", sign);
    }

    private static String httpPost(String path, String json) throws Exception {
        String url = HttpReporter.baseUrl() + path;
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setConnectTimeout(8000);
        conn.setReadTimeout(12000);
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        conn.setFixedLengthStreamingMode(bytes.length);
        OutputStream os = conn.getOutputStream();
        os.write(bytes);
        os.flush();
        os.close();
        InputStream in = conn.getResponseCode() >= 400 ? conn.getErrorStream() : conn.getInputStream();
        String text = readAll(in);
        conn.disconnect();
        return text;
    }

    private static String readAll(InputStream in) throws Exception {
        if (in == null) {
            return "";
        }
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte[] tmp = new byte[4096];
        int n;
        while ((n = in.read(tmp)) > 0) {
            buf.write(tmp, 0, n);
        }
        in.close();
        return new String(buf.toByteArray(), StandardCharsets.UTF_8);
    }

    private static String toPem(String type, byte[] der) {
        String b64 = toB64(der);
        StringBuilder sb = new StringBuilder();
        sb.append("-----BEGIN ").append(type).append("-----\n");
        for (int i = 0; i < b64.length(); i += 64) {
            sb.append(b64, i, Math.min(i + 64, b64.length())).append('\n');
        }
        sb.append("-----END ").append(type).append("-----\n");
        return sb.toString();
    }

    private static byte[] fromPem(String pem) {
        String stripped = pem.replaceAll("-----BEGIN [A-Z ]+-----", "")
                .replaceAll("-----END [A-Z ]+-----", "")
                .replaceAll("\\s", "");
        return fromB64(stripped);
    }

    private static String toB64(byte[] data) {
        final char[] tbl = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".toCharArray();
        StringBuilder sb = new StringBuilder(((data.length + 2) / 3) * 4);
        int i = 0;
        while (i + 2 < data.length) {
            int n = ((data[i] & 0xff) << 16) | ((data[i + 1] & 0xff) << 8) | (data[i + 2] & 0xff);
            sb.append(tbl[(n >>> 18) & 63]).append(tbl[(n >>> 12) & 63])
                    .append(tbl[(n >>> 6) & 63]).append(tbl[n & 63]);
            i += 3;
        }
        if (i < data.length) {
            int n = (data[i] & 0xff) << 16;
            sb.append(tbl[(n >>> 18) & 63]);
            if (i + 1 < data.length) {
                n |= (data[i + 1] & 0xff) << 8;
                sb.append(tbl[(n >>> 12) & 63]).append(tbl[(n >>> 6) & 63]).append('=');
            } else {
                sb.append(tbl[(n >>> 12) & 63]).append("==");
            }
        }
        return sb.toString();
    }

    private static byte[] fromB64(String s) {
        String clean = s.replaceAll("[^A-Za-z0-9+/=]", "");
        int pad = clean.endsWith("==") ? 2 : clean.endsWith("=") ? 1 : 0;
        int outLen = (clean.length() / 4) * 3 - pad;
        byte[] out = new byte[Math.max(outLen, 0)];
        int[] map = new int[128];
        for (int i = 0; i < 128; i++) {
            map[i] = -1;
        }
        String tbl = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        for (int i = 0; i < 64; i++) {
            map[tbl.charAt(i)] = i;
        }
        int o = 0;
        for (int i = 0; i + 3 < clean.length(); i += 4) {
            int n = (map[clean.charAt(i)] << 18) | (map[clean.charAt(i + 1)] << 12)
                    | (Math.max(map[clean.charAt(i + 2)], 0) << 6) | Math.max(map[clean.charAt(i + 3)], 0);
            if (o < out.length) {
                out[o++] = (byte) (n >>> 16);
            }
            if (o < out.length) {
                out[o++] = (byte) (n >>> 8);
            }
            if (o < out.length) {
                out[o++] = (byte) n;
            }
        }
        return out;
    }

    /** Compact sorted JSON matching Python json.dumps(..., sort_keys=True, separators=(",",":")). */
    private static String sortedJson(JSONObject obj) throws Exception {
        ArrayList<String> keys = new ArrayList<>();
        Iterator<?> it = obj.keys();
        while (it.hasNext()) {
            String k = String.valueOf(it.next());
            if (!"sig".equals(k)) {
                keys.add(k);
            }
        }
        Collections.sort(keys);
        StringBuilder sb = new StringBuilder("{");
        for (int i = 0; i < keys.size(); i++) {
            if (i > 0) {
                sb.append(',');
            }
            String k = keys.get(i);
            sb.append(JSONObject.quote(k)).append(':').append(jsonValue(obj.get(k)));
        }
        sb.append('}');
        return sb.toString();
    }

    private static String jsonValue(Object v) throws Exception {
        if (v == null || v == JSONObject.NULL) {
            return "null";
        }
        if (v instanceof JSONObject) {
            return sortedJson((JSONObject) v);
        }
        if (v instanceof org.json.JSONArray) {
            org.json.JSONArray arr = (org.json.JSONArray) v;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < arr.length(); i++) {
                if (i > 0) {
                    sb.append(',');
                }
                sb.append(jsonValue(arr.get(i)));
            }
            sb.append(']');
            return sb.toString();
        }
        if (v instanceof Number || v instanceof Boolean) {
            return String.valueOf(v);
        }
        return JSONObject.quote(String.valueOf(v));
    }

    private static String toHex(byte[] data) {
        char[] hex = "0123456789abcdef".toCharArray();
        char[] out = new char[data.length * 2];
        for (int i = 0; i < data.length; i++) {
            int v = data[i] & 0xff;
            out[i * 2] = hex[v >>> 4];
            out[i * 2 + 1] = hex[v & 0x0f];
        }
        return new String(out);
    }
}
