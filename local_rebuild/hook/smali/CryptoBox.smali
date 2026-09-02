.class public final Lcom/dingtalk/groupbill/net/CryptoBox;
.super Ljava/lang/Object;
.source "CryptoBox.java"


# static fields
.field private static final LOCK:Ljava/lang/Object;

.field private static final OAEP:Ljavax/crypto/spec/OAEPParameterSpec;

.field private static accountId:Ljava/lang/String;

.field private static deviceId:Ljava/lang/String;

.field private static devicePrivateKey:Ljava/security/PrivateKey;

.field private static enrolled:Z

.field private static hmacSecret:[B

.field private static nickName:Ljava/lang/String;

.field private static serverPublicKey:Ljava/security/PublicKey;

.field private static userId:Ljava/lang/String;


# direct methods
.method static constructor <clinit>()V
    .registers 5

    .line 45
    new-instance v0, Ljavax/crypto/spec/OAEPParameterSpec;

    sget-object v1, Ljava/security/spec/MGF1ParameterSpec;->SHA256:Ljava/security/spec/MGF1ParameterSpec;

    sget-object v2, Ljavax/crypto/spec/PSource$PSpecified;->DEFAULT:Ljavax/crypto/spec/PSource$PSpecified;

    const-string v3, "SHA-256"

    const-string v4, "MGF1"

    invoke-direct {v0, v3, v4, v1, v2}, Ljavax/crypto/spec/OAEPParameterSpec;-><init>(Ljava/lang/String;Ljava/lang/String;Ljava/security/spec/AlgorithmParameterSpec;Ljavax/crypto/spec/PSource;)V

    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->OAEP:Ljavax/crypto/spec/OAEPParameterSpec;

    .line 47
    new-instance v0, Ljava/lang/Object;

    invoke-direct {v0}, Ljava/lang/Object;-><init>()V

    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    .line 48
    const-string v0, ""

    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->userId:Ljava/lang/String;

    .line 49
    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->accountId:Ljava/lang/String;

    .line 50
    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->nickName:Ljava/lang/String;

    .line 51
    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->deviceId:Ljava/lang/String;

    return-void
.end method

.method private constructor <init>()V
    .registers 1

    .line 57
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method private static applySignHeaders(Ljava/net/HttpURLConnection;Ljava/lang/String;Ljava/lang/String;[B)V
    .registers 9
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 249
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v0

    const-wide/16 v2, 0x3e8

    div-long/2addr v0, v2

    .line 250
    invoke-static {}, Ljava/util/UUID;->randomUUID()Ljava/util/UUID;

    move-result-object v2

    invoke-virtual {v2}, Ljava/util/UUID;->toString()Ljava/lang/String;

    move-result-object v2

    const-string v3, "-"

    const-string v4, ""

    invoke-virtual {v2, v3, v4}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;

    move-result-object v2

    .line 251
    const-string v3, "SHA-256"

    invoke-static {v3}, Ljava/security/MessageDigest;->getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;

    move-result-object v3

    .line 252
    invoke-virtual {v3, p3}, Ljava/security/MessageDigest;->digest([B)[B

    move-result-object p3

    invoke-static {p3}, Lcom/dingtalk/groupbill/net/CryptoBox;->toHex([B)Ljava/lang/String;

    move-result-object p3

    .line 253
    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {p1}, Ljava/lang/String;->toUpperCase()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v3, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    const-string v3, "\n"

    invoke-virtual {p1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, v0, v1}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    .line 254
    const-string p2, "HmacSHA256"

    invoke-static {p2}, Ljavax/crypto/Mac;->getInstance(Ljava/lang/String;)Ljavax/crypto/Mac;

    move-result-object p3

    .line 255
    new-instance v3, Ljavax/crypto/spec/SecretKeySpec;

    sget-object v4, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    invoke-direct {v3, v4, p2}, Ljavax/crypto/spec/SecretKeySpec;-><init>([BLjava/lang/String;)V

    invoke-virtual {p3, v3}, Ljavax/crypto/Mac;->init(Ljava/security/Key;)V

    .line 256
    sget-object p2, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p1, p2}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p1

    invoke-virtual {p3, p1}, Ljavax/crypto/Mac;->doFinal([B)[B

    move-result-object p1

    invoke-static {p1}, Lcom/dingtalk/groupbill/net/CryptoBox;->toHex([B)Ljava/lang/String;

    move-result-object p1

    .line 257
    const-string p2, "X-Device-Id"

    sget-object p3, Lcom/dingtalk/groupbill/net/CryptoBox;->deviceId:Ljava/lang/String;

    invoke-virtual {p0, p2, p3}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 258
    const-string p2, "X-Timestamp"

    invoke-static {v0, v1}, Ljava/lang/String;->valueOf(J)Ljava/lang/String;

    move-result-object p3

    invoke-virtual {p0, p2, p3}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 259
    const-string p2, "X-Nonce"

    invoke-virtual {p0, p2, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 260
    const-string p2, "X-Sign"

    invoke-virtual {p0, p2, p1}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 261
    return-void
.end method

.method private static doEnrollLocked()V
    .registers 7
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 198
    const-string v0, "RSA"

    invoke-static {v0}, Ljava/security/KeyPairGenerator;->getInstance(Ljava/lang/String;)Ljava/security/KeyPairGenerator;

    move-result-object v1

    .line 199
    new-instance v2, Ljava/security/SecureRandom;

    invoke-direct {v2}, Ljava/security/SecureRandom;-><init>()V

    const/16 v3, 0x800

    invoke-virtual {v1, v3, v2}, Ljava/security/KeyPairGenerator;->initialize(ILjava/security/SecureRandom;)V

    .line 200
    invoke-virtual {v1}, Ljava/security/KeyPairGenerator;->generateKeyPair()Ljava/security/KeyPair;

    move-result-object v1

    .line 201
    invoke-virtual {v1}, Ljava/security/KeyPair;->getPrivate()Ljava/security/PrivateKey;

    move-result-object v2

    sput-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->devicePrivateKey:Ljava/security/PrivateKey;

    .line 202
    invoke-virtual {v1}, Ljava/security/KeyPair;->getPublic()Ljava/security/PublicKey;

    move-result-object v1

    invoke-interface {v1}, Ljava/security/PublicKey;->getEncoded()[B

    move-result-object v1

    const-string v2, "PUBLIC KEY"

    invoke-static {v2, v1}, Lcom/dingtalk/groupbill/net/CryptoBox;->toPem(Ljava/lang/String;[B)Ljava/lang/String;

    move-result-object v1

    .line 204
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2}, Lorg/json/JSONObject;-><init>()V

    .line 205
    const-string v3, "userId"

    sget-object v4, Lcom/dingtalk/groupbill/net/CryptoBox;->userId:Ljava/lang/String;

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 206
    const-string v3, "accountId"

    sget-object v4, Lcom/dingtalk/groupbill/net/CryptoBox;->accountId:Ljava/lang/String;

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 207
    const-string v3, "devicePublicKey"

    invoke-virtual {v2, v3, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 208
    const-string v1, "/api/device/enroll"

    invoke-virtual {v2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object v2

    invoke-static {v1, v2}, Lcom/dingtalk/groupbill/net/CryptoBox;->httpPost(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    .line 209
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2, v1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 210
    const/4 v1, -0x1

    const-string v3, "code"

    invoke-virtual {v2, v3, v1}, Lorg/json/JSONObject;->optInt(Ljava/lang/String;I)I

    move-result v1

    if-nez v1, :cond_a1

    .line 213
    const-string v1, "data"

    invoke-virtual {v2, v1}, Lorg/json/JSONObject;->getJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v1

    .line 214
    const-string v2, "device_id"

    invoke-virtual {v1, v2}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    sput-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->deviceId:Ljava/lang/String;

    .line 215
    const-string v2, "enc_hmac_secret"

    invoke-virtual {v1, v2}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    .line 216
    const-string v3, "server_public_key"

    invoke-virtual {v1, v3}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    .line 218
    const-string v3, "RSA/ECB/OAEPPadding"

    invoke-static {v3}, Ljavax/crypto/Cipher;->getInstance(Ljava/lang/String;)Ljavax/crypto/Cipher;

    move-result-object v3

    .line 219
    sget-object v4, Lcom/dingtalk/groupbill/net/CryptoBox;->devicePrivateKey:Ljava/security/PrivateKey;

    sget-object v5, Lcom/dingtalk/groupbill/net/CryptoBox;->OAEP:Ljavax/crypto/spec/OAEPParameterSpec;

    const/4 v6, 0x2

    invoke-virtual {v3, v6, v4, v5}, Ljavax/crypto/Cipher;->init(ILjava/security/Key;Ljava/security/spec/AlgorithmParameterSpec;)V

    .line 220
    invoke-static {v2}, Lcom/dingtalk/groupbill/net/CryptoBox;->fromB64(Ljava/lang/String;)[B

    move-result-object v2

    invoke-virtual {v3, v2}, Ljavax/crypto/Cipher;->doFinal([B)[B

    move-result-object v2

    sput-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    .line 221
    invoke-static {v0}, Ljava/security/KeyFactory;->getInstance(Ljava/lang/String;)Ljava/security/KeyFactory;

    move-result-object v0

    new-instance v2, Ljava/security/spec/X509EncodedKeySpec;

    .line 222
    invoke-static {v1}, Lcom/dingtalk/groupbill/net/CryptoBox;->fromPem(Ljava/lang/String;)[B

    move-result-object v1

    invoke-direct {v2, v1}, Ljava/security/spec/X509EncodedKeySpec;-><init>([B)V

    .line 221
    invoke-virtual {v0, v2}, Ljava/security/KeyFactory;->generatePublic(Ljava/security/spec/KeySpec;)Ljava/security/PublicKey;

    move-result-object v0

    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->serverPublicKey:Ljava/security/PublicKey;

    .line 223
    const/4 v0, 0x1

    sput-boolean v0, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    .line 224
    return-void

    .line 211
    :cond_a1
    new-instance v0, Ljava/lang/IllegalStateException;

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "enroll code="

    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v2, v3}, Lorg/json/JSONObject;->optInt(Ljava/lang/String;)I

    move-result v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-direct {v0, v1}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V

    throw v0
.end method

.method private static encryptHybrid([B)Lorg/json/JSONObject;
    .registers 7
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 227
    const-string v0, "AES"

    invoke-static {v0}, Ljavax/crypto/KeyGenerator;->getInstance(Ljava/lang/String;)Ljavax/crypto/KeyGenerator;

    move-result-object v0

    .line 228
    new-instance v1, Ljava/security/SecureRandom;

    invoke-direct {v1}, Ljava/security/SecureRandom;-><init>()V

    const/16 v2, 0x100

    invoke-virtual {v0, v2, v1}, Ljavax/crypto/KeyGenerator;->init(ILjava/security/SecureRandom;)V

    .line 229
    invoke-virtual {v0}, Ljavax/crypto/KeyGenerator;->generateKey()Ljavax/crypto/SecretKey;

    move-result-object v0

    .line 230
    const/16 v1, 0xc

    new-array v1, v1, [B

    .line 231
    new-instance v2, Ljava/security/SecureRandom;

    invoke-direct {v2}, Ljava/security/SecureRandom;-><init>()V

    invoke-virtual {v2, v1}, Ljava/security/SecureRandom;->nextBytes([B)V

    .line 232
    const-string v2, "AES/GCM/NoPadding"

    invoke-static {v2}, Ljavax/crypto/Cipher;->getInstance(Ljava/lang/String;)Ljavax/crypto/Cipher;

    move-result-object v2

    .line 233
    new-instance v3, Ljavax/crypto/spec/GCMParameterSpec;

    const/16 v4, 0x80

    invoke-direct {v3, v4, v1}, Ljavax/crypto/spec/GCMParameterSpec;-><init>(I[B)V

    const/4 v4, 0x1

    invoke-virtual {v2, v4, v0, v3}, Ljavax/crypto/Cipher;->init(ILjava/security/Key;Ljava/security/spec/AlgorithmParameterSpec;)V

    .line 234
    invoke-virtual {v2, p0}, Ljavax/crypto/Cipher;->doFinal([B)[B

    move-result-object p0

    .line 236
    const-string v2, "RSA/ECB/OAEPPadding"

    invoke-static {v2}, Ljavax/crypto/Cipher;->getInstance(Ljava/lang/String;)Ljavax/crypto/Cipher;

    move-result-object v2

    .line 237
    sget-object v3, Lcom/dingtalk/groupbill/net/CryptoBox;->serverPublicKey:Ljava/security/PublicKey;

    sget-object v5, Lcom/dingtalk/groupbill/net/CryptoBox;->OAEP:Ljavax/crypto/spec/OAEPParameterSpec;

    invoke-virtual {v2, v4, v3, v5}, Ljavax/crypto/Cipher;->init(ILjava/security/Key;Ljava/security/spec/AlgorithmParameterSpec;)V

    .line 238
    invoke-interface {v0}, Ljavax/crypto/SecretKey;->getEncoded()[B

    move-result-object v0

    invoke-virtual {v2, v0}, Ljavax/crypto/Cipher;->doFinal([B)[B

    move-result-object v0

    .line 240
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2}, Lorg/json/JSONObject;-><init>()V

    .line 241
    const-string v3, "ek"

    invoke-static {v0}, Lcom/dingtalk/groupbill/net/CryptoBox;->toB64([B)Ljava/lang/String;

    move-result-object v0

    invoke-virtual {v2, v3, v0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 242
    const-string v0, "iv"

    invoke-static {v1}, Lcom/dingtalk/groupbill/net/CryptoBox;->toB64([B)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v2, v0, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 243
    const-string v0, "ct"

    invoke-static {p0}, Lcom/dingtalk/groupbill/net/CryptoBox;->toB64([B)Ljava/lang/String;

    move-result-object p0

    invoke-virtual {v2, v0, p0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 244
    return-object v2
.end method

.method public static ensureEnrolled()V
    .registers 9

    .line 111
    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v0

    .line 112
    :try_start_3
    sget-boolean v1, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    if-nez v1, :cond_3e

    sget-object v1, Lcom/dingtalk/groupbill/net/CryptoBox;->userId:Ljava/lang/String;

    invoke-virtual {v1}, Ljava/lang/String;->isEmpty()Z

    move-result v1
    :try_end_d
    .catchall {:try_start_3 .. :try_end_d} :catchall_40

    if-eqz v1, :cond_10

    goto :goto_3e

    .line 116
    :cond_10
    :try_start_10
    invoke-static {}, Lcom/dingtalk/groupbill/net/CryptoBox;->doEnrollLocked()V
    :try_end_13
    .catchall {:try_start_10 .. :try_end_13} :catchall_14

    .line 125
    goto :goto_3c

    .line 117
    :catchall_14
    move-exception v1

    .line 119
    :try_start_15
    const-string v2, "com.dingtalk.groupbill.util.DtLog"

    invoke-static {v2}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;

    move-result-object v2

    const-string v3, "e"

    const/4 v4, 0x2

    new-array v5, v4, [Ljava/lang/Class;

    const-class v6, Ljava/lang/String;

    const/4 v7, 0x0

    aput-object v6, v5, v7

    const-class v6, Ljava/lang/Throwable;

    const/4 v8, 0x1

    aput-object v6, v5, v8

    .line 120
    invoke-virtual {v2, v3, v5}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v2

    new-array v3, v4, [Ljava/lang/Object;

    const-string v4, "CryptoBox enroll FAILED"

    aput-object v4, v3, v7

    aput-object v1, v3, v8

    .line 121
    const/4 v1, 0x0

    invoke-virtual {v2, v1, v3}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;
    :try_end_3a
    .catchall {:try_start_15 .. :try_end_3a} :catchall_3b

    .line 124
    goto :goto_3c

    .line 122
    :catchall_3b
    move-exception v1

    .line 126
    :goto_3c
    :try_start_3c
    monitor-exit v0

    .line 127
    return-void

    .line 113
    :cond_3e
    :goto_3e
    monitor-exit v0

    return-void

    .line 126
    :catchall_40
    move-exception v1

    monitor-exit v0
    :try_end_42
    .catchall {:try_start_3c .. :try_end_42} :catchall_40

    throw v1
.end method

.method private static fetchNick()V
    .registers 5

    .line 83
    :try_start_0
    const-string v0, "com.alibaba.android.dingtalk.userbase.UserEngineInterface"

    invoke-static {v0}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;

    move-result-object v0

    .line 84
    const-string v1, "f"

    const/4 v2, 0x0

    new-array v3, v2, [Ljava/lang/Class;

    invoke-virtual {v0, v1, v3}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v1

    new-array v3, v2, [Ljava/lang/Object;

    const/4 v4, 0x0

    invoke-virtual {v1, v4, v3}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v1

    .line 85
    if-nez v1, :cond_19

    .line 86
    return-void

    .line 88
    :cond_19
    const-string v3, "e"

    new-array v4, v2, [Ljava/lang/Class;

    invoke-virtual {v0, v3, v4}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v0

    new-array v2, v2, [Ljava/lang/Object;

    invoke-virtual {v0, v1, v2}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v0

    .line 89
    if-nez v0, :cond_2a

    .line 90
    return-void

    .line 92
    :cond_2a
    invoke-virtual {v0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v1

    const-string v2, "nick"

    invoke-virtual {v1, v2}, Ljava/lang/Class;->getField(Ljava/lang/String;)Ljava/lang/reflect/Field;

    move-result-object v1

    invoke-virtual {v1, v0}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v0

    .line 93
    instance-of v1, v0, Ljava/lang/String;

    if-eqz v1, :cond_51

    move-object v1, v0

    check-cast v1, Ljava/lang/String;

    invoke-virtual {v1}, Ljava/lang/String;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_51

    .line 94
    sget-object v1, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v1
    :try_end_48
    .catchall {:try_start_0 .. :try_end_48} :catchall_52

    .line 95
    :try_start_48
    check-cast v0, Ljava/lang/String;

    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->nickName:Ljava/lang/String;

    .line 96
    monitor-exit v1

    goto :goto_51

    :catchall_4e
    move-exception v0

    monitor-exit v1
    :try_end_50
    .catchall {:try_start_48 .. :try_end_50} :catchall_4e

    :try_start_50
    throw v0
    :try_end_51
    .catchall {:try_start_50 .. :try_end_51} :catchall_52

    .line 100
    :cond_51
    :goto_51
    goto :goto_53

    .line 98
    :catchall_52
    move-exception v0

    .line 101
    :goto_53
    return-void
.end method

.method private static fromB64(Ljava/lang/String;)[B
    .registers 10

    .line 339
    const-string v0, "[^A-Za-z0-9+/=]"

    const-string v1, ""

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 340
    const-string v0, "=="

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    const/4 v1, 0x0

    if-eqz v0, :cond_13

    const/4 v0, 0x2

    goto :goto_1e

    :cond_13
    const-string v0, "="

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_1d

    const/4 v0, 0x1

    goto :goto_1e

    :cond_1d
    const/4 v0, 0x0

    .line 341
    :goto_1e
    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result v2

    div-int/lit8 v2, v2, 0x4

    mul-int/lit8 v2, v2, 0x3

    sub-int/2addr v2, v0

    .line 342
    invoke-static {v2, v1}, Ljava/lang/Math;->max(II)I

    move-result v0

    new-array v2, v0, [B

    .line 343
    const/16 v3, 0x80

    new-array v4, v3, [I

    .line 344
    const/4 v5, 0x0

    :goto_32
    if-ge v5, v3, :cond_3a

    .line 345
    const/4 v6, -0x1

    aput v6, v4, v5

    .line 344
    add-int/lit8 v5, v5, 0x1

    goto :goto_32

    .line 347
    :cond_3a
    nop

    .line 348
    const/4 v3, 0x0

    :goto_3c
    const/16 v5, 0x40

    if-ge v3, v5, :cond_4b

    .line 349
    const-string v5, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    invoke-virtual {v5, v3}, Ljava/lang/String;->charAt(I)C

    move-result v5

    aput v3, v4, v5

    .line 348
    add-int/lit8 v3, v3, 0x1

    goto :goto_3c

    .line 351
    :cond_4b
    nop

    .line 352
    const/4 v3, 0x0

    const/4 v5, 0x0

    :goto_4e
    add-int/lit8 v6, v3, 0x3

    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result v7

    if-ge v6, v7, :cond_a2

    .line 353
    invoke-virtual {p0, v3}, Ljava/lang/String;->charAt(I)C

    move-result v7

    aget v7, v4, v7

    shl-int/lit8 v7, v7, 0x12

    add-int/lit8 v8, v3, 0x1

    invoke-virtual {p0, v8}, Ljava/lang/String;->charAt(I)C

    move-result v8

    aget v8, v4, v8

    shl-int/lit8 v8, v8, 0xc

    or-int/2addr v7, v8

    add-int/lit8 v8, v3, 0x2

    .line 354
    invoke-virtual {p0, v8}, Ljava/lang/String;->charAt(I)C

    move-result v8

    aget v8, v4, v8

    invoke-static {v8, v1}, Ljava/lang/Math;->max(II)I

    move-result v8

    shl-int/lit8 v8, v8, 0x6

    or-int/2addr v7, v8

    invoke-virtual {p0, v6}, Ljava/lang/String;->charAt(I)C

    move-result v6

    aget v6, v4, v6

    invoke-static {v6, v1}, Ljava/lang/Math;->max(II)I

    move-result v6

    or-int/2addr v6, v7

    .line 355
    if-ge v5, v0, :cond_8d

    .line 356
    add-int/lit8 v7, v5, 0x1

    ushr-int/lit8 v8, v6, 0x10

    int-to-byte v8, v8

    aput-byte v8, v2, v5

    move v5, v7

    .line 358
    :cond_8d
    if-ge v5, v0, :cond_97

    .line 359
    add-int/lit8 v7, v5, 0x1

    ushr-int/lit8 v8, v6, 0x8

    int-to-byte v8, v8

    aput-byte v8, v2, v5

    move v5, v7

    .line 361
    :cond_97
    if-ge v5, v0, :cond_9f

    .line 362
    add-int/lit8 v7, v5, 0x1

    int-to-byte v6, v6

    aput-byte v6, v2, v5

    move v5, v7

    .line 352
    :cond_9f
    add-int/lit8 v3, v3, 0x4

    goto :goto_4e

    .line 365
    :cond_a2
    return-object v2
.end method

.method private static fromPem(Ljava/lang/String;)[B
    .registers 3

    .line 309
    const-string v0, "-----BEGIN [A-Z ]+-----"

    const-string v1, ""

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 310
    const-string v0, "-----END [A-Z ]+-----"

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 311
    const-string v0, "\\s"

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 312
    invoke-static {p0}, Lcom/dingtalk/groupbill/net/CryptoBox;->fromB64(Ljava/lang/String;)[B

    move-result-object p0

    return-object p0
.end method

.method private static httpPost(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 4
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 264
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    invoke-static {}, Lcom/dingtalk/groupbill/net/HttpReporter;->baseUrl()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    .line 265
    new-instance v0, Ljava/net/URL;

    invoke-direct {v0, p0}, Ljava/net/URL;-><init>(Ljava/lang/String;)V

    invoke-virtual {v0}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;

    move-result-object p0

    check-cast p0, Ljava/net/HttpURLConnection;

    .line 266
    const/16 v0, 0x1f40

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setConnectTimeout(I)V

    .line 267
    const/16 v0, 0x2ee0

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setReadTimeout(I)V

    .line 268
    const-string v0, "POST"

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setRequestMethod(Ljava/lang/String;)V

    .line 269
    const/4 v0, 0x1

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setDoOutput(Z)V

    .line 270
    const-string v0, "Content-Type"

    const-string v1, "application/json; charset=utf-8"

    invoke-virtual {p0, v0, v1}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 271
    sget-object v0, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p1, v0}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p1

    .line 272
    array-length v0, p1

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setFixedLengthStreamingMode(I)V

    .line 273
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getOutputStream()Ljava/io/OutputStream;

    move-result-object v0

    .line 274
    invoke-virtual {v0, p1}, Ljava/io/OutputStream;->write([B)V

    .line 275
    invoke-virtual {v0}, Ljava/io/OutputStream;->flush()V

    .line 276
    invoke-virtual {v0}, Ljava/io/OutputStream;->close()V

    .line 277
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getResponseCode()I

    move-result p1

    const/16 v0, 0x190

    if-lt p1, v0, :cond_5e

    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getErrorStream()Ljava/io/InputStream;

    move-result-object p1

    goto :goto_62

    :cond_5e
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getInputStream()Ljava/io/InputStream;

    move-result-object p1

    .line 278
    :goto_62
    invoke-static {p1}, Lcom/dingtalk/groupbill/net/CryptoBox;->readAll(Ljava/io/InputStream;)Ljava/lang/String;

    move-result-object p1

    .line 279
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->disconnect()V

    .line 280
    return-object p1
.end method

.method private static jsonValue(Ljava/lang/Object;)Ljava/lang/String;
    .registers 4
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 392
    if-eqz p0, :cond_5c

    sget-object v0, Lorg/json/JSONObject;->NULL:Ljava/lang/Object;

    if-ne p0, v0, :cond_7

    goto :goto_5c

    .line 395
    :cond_7
    instance-of v0, p0, Lorg/json/JSONObject;

    if-eqz v0, :cond_12

    .line 396
    check-cast p0, Lorg/json/JSONObject;

    invoke-static {p0}, Lcom/dingtalk/groupbill/net/CryptoBox;->sortedJson(Lorg/json/JSONObject;)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 398
    :cond_12
    instance-of v0, p0, Lorg/json/JSONArray;

    if-eqz v0, :cond_45

    .line 399
    check-cast p0, Lorg/json/JSONArray;

    .line 400
    new-instance v0, Ljava/lang/StringBuilder;

    const-string v1, "["

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    .line 401
    const/4 v1, 0x0

    :goto_20
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-ge v1, v2, :cond_3b

    .line 402
    if-lez v1, :cond_2d

    .line 403
    const/16 v2, 0x2c

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 405
    :cond_2d
    invoke-virtual {p0, v1}, Lorg/json/JSONArray;->get(I)Ljava/lang/Object;

    move-result-object v2

    invoke-static {v2}, Lcom/dingtalk/groupbill/net/CryptoBox;->jsonValue(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 401
    add-int/lit8 v1, v1, 0x1

    goto :goto_20

    .line 407
    :cond_3b
    const/16 p0, 0x5d

    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 408
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 410
    :cond_45
    instance-of v0, p0, Ljava/lang/Number;

    if-nez v0, :cond_57

    instance-of v0, p0, Ljava/lang/Boolean;

    if-eqz v0, :cond_4e

    goto :goto_57

    .line 413
    :cond_4e
    invoke-static {p0}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object p0

    invoke-static {p0}, Lorg/json/JSONObject;->quote(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 411
    :cond_57
    :goto_57
    invoke-static {p0}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 393
    :cond_5c
    :goto_5c
    const-string p0, "null"

    return-object p0
.end method

.method public static nick()Ljava/lang/String;
    .registers 2

    .line 105
    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v0

    .line 106
    :try_start_3
    sget-object v1, Lcom/dingtalk/groupbill/net/CryptoBox;->nickName:Ljava/lang/String;

    monitor-exit v0

    return-object v1

    .line 107
    :catchall_7
    move-exception v1

    monitor-exit v0
    :try_end_9
    .catchall {:try_start_3 .. :try_end_9} :catchall_7

    throw v1
.end method

.method public static prepareHttp(Ljava/net/HttpURLConnection;Ljava/lang/String;Lorg/json/JSONObject;)[B
    .registers 6

    .line 135
    invoke-virtual {p2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object v0

    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {v0, v1}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object v0

    .line 137
    :try_start_a
    invoke-static {}, Lcom/dingtalk/groupbill/net/CryptoBox;->ensureEnrolled()V

    .line 138
    sget-object v1, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v1
    :try_end_10
    .catchall {:try_start_a .. :try_end_10} :catchall_41

    .line 139
    :try_start_10
    sget-boolean v2, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    if-eqz v2, :cond_3c

    sget-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    if-eqz v2, :cond_3c

    sget-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->serverPublicKey:Ljava/security/PublicKey;

    if-nez v2, :cond_1d

    goto :goto_3c

    .line 142
    :cond_1d
    monitor-exit v1
    :try_end_1e
    .catchall {:try_start_10 .. :try_end_1e} :catchall_3e

    .line 143
    :try_start_1e
    invoke-virtual {p2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p2

    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p2, v1}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p2

    invoke-static {p2}, Lcom/dingtalk/groupbill/net/CryptoBox;->encryptHybrid([B)Lorg/json/JSONObject;

    move-result-object p2

    .line 144
    invoke-virtual {p2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p2

    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p2, v1}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p2

    .line 145
    const-string v1, "POST"

    invoke-static {p0, v1, p1, p2}, Lcom/dingtalk/groupbill/net/CryptoBox;->applySignHeaders(Ljava/net/HttpURLConnection;Ljava/lang/String;Ljava/lang/String;[B)V
    :try_end_3b
    .catchall {:try_start_1e .. :try_end_3b} :catchall_41

    .line 146
    return-object p2

    .line 140
    :cond_3c
    :goto_3c
    :try_start_3c
    monitor-exit v1

    return-object v0

    .line 142
    :catchall_3e
    move-exception p0

    monitor-exit v1
    :try_end_40
    .catchall {:try_start_3c .. :try_end_40} :catchall_3e

    :try_start_40
    throw p0
    :try_end_41
    .catchall {:try_start_40 .. :try_end_41} :catchall_41

    .line 147
    :catchall_41
    move-exception p0

    .line 148
    return-object v0
.end method

.method private static readAll(Ljava/io/InputStream;)Ljava/lang/String;
    .registers 5
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 284
    if-nez p0, :cond_5

    .line 285
    const-string p0, ""

    return-object p0

    .line 287
    :cond_5
    new-instance v0, Ljava/io/ByteArrayOutputStream;

    invoke-direct {v0}, Ljava/io/ByteArrayOutputStream;-><init>()V

    .line 288
    const/16 v1, 0x1000

    new-array v1, v1, [B

    .line 290
    :goto_e
    invoke-virtual {p0, v1}, Ljava/io/InputStream;->read([B)I

    move-result v2

    if-lez v2, :cond_19

    .line 291
    const/4 v3, 0x0

    invoke-virtual {v0, v1, v3, v2}, Ljava/io/ByteArrayOutputStream;->write([BII)V

    goto :goto_e

    .line 293
    :cond_19
    invoke-virtual {p0}, Ljava/io/InputStream;->close()V

    .line 294
    new-instance p0, Ljava/lang/String;

    invoke-virtual {v0}, Ljava/io/ByteArrayOutputStream;->toByteArray()[B

    move-result-object v0

    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-direct {p0, v0, v1}, Ljava/lang/String;-><init>([BLjava/nio/charset/Charset;)V

    return-object p0
.end method

.method public static setIdentity(Ljava/lang/String;Ljava/lang/String;)V
    .registers 4

    .line 60
    if-eqz p0, :cond_2f

    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_9

    goto :goto_2f

    .line 63
    :cond_9
    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v0

    .line 64
    :try_start_c
    sget-object v1, Lcom/dingtalk/groupbill/net/CryptoBox;->userId:Ljava/lang/String;

    invoke-virtual {p0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-nez v1, :cond_17

    .line 65
    const/4 v1, 0x0

    sput-boolean v1, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    .line 67
    :cond_17
    sput-object p0, Lcom/dingtalk/groupbill/net/CryptoBox;->userId:Ljava/lang/String;

    .line 68
    if-nez p1, :cond_1d

    const-string p1, ""

    :cond_1d
    sput-object p1, Lcom/dingtalk/groupbill/net/CryptoBox;->accountId:Ljava/lang/String;

    .line 69
    monitor-exit v0
    :try_end_20
    .catchall {:try_start_c .. :try_end_20} :catchall_2c

    .line 71
    sget-object p0, Lcom/dingtalk/groupbill/net/CryptoBox;->nickName:Ljava/lang/String;

    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result p0

    if-eqz p0, :cond_2b

    .line 72
    invoke-static {}, Lcom/dingtalk/groupbill/net/CryptoBox;->fetchNick()V

    .line 74
    :cond_2b
    return-void

    .line 69
    :catchall_2c
    move-exception p0

    :try_start_2d
    monitor-exit v0
    :try_end_2e
    .catchall {:try_start_2d .. :try_end_2e} :catchall_2c

    throw p0

    .line 61
    :cond_2f
    :goto_2f
    return-void
.end method

.method public static signWsData(Ljava/lang/String;Lorg/json/JSONObject;)V
    .registers 7

    .line 154
    if-eqz p1, :cond_a0

    if-nez p0, :cond_6

    goto/16 :goto_a0

    .line 158
    :cond_6
    const-string v0, "register"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_25

    .line 160
    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v0

    .line 161
    :try_start_11
    sget-object p0, Lcom/dingtalk/groupbill/net/CryptoBox;->nickName:Ljava/lang/String;

    .line 162
    monitor-exit v0
    :try_end_14
    .catchall {:try_start_11 .. :try_end_14} :catchall_22

    .line 163
    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-nez v0, :cond_21

    .line 165
    :try_start_1a
    const-string v0, "nick"

    invoke-virtual {p1, v0, p0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    :try_end_1f
    .catchall {:try_start_1a .. :try_end_1f} :catchall_20

    .line 167
    goto :goto_21

    .line 166
    :catchall_20
    move-exception p0

    .line 169
    :cond_21
    :goto_21
    return-void

    .line 162
    :catchall_22
    move-exception p0

    :try_start_23
    monitor-exit v0
    :try_end_24
    .catchall {:try_start_23 .. :try_end_24} :catchall_22

    throw p0

    .line 171
    :cond_25
    const-string v0, "bill.upsert"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_3e

    const-string v0, "alipay.upload"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_3e

    const-string v0, "rpc.result"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p0

    if-nez p0, :cond_3e

    .line 172
    return-void

    .line 175
    :cond_3e
    :try_start_3e
    invoke-static {}, Lcom/dingtalk/groupbill/net/CryptoBox;->ensureEnrolled()V

    .line 177
    sget-object p0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter p0
    :try_end_44
    .catchall {:try_start_3e .. :try_end_44} :catchall_9e

    .line 178
    :try_start_44
    sget-boolean v0, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    if-eqz v0, :cond_99

    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    if-nez v0, :cond_4d

    goto :goto_99

    .line 181
    :cond_4d
    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    .line 182
    monitor-exit p0
    :try_end_50
    .catchall {:try_start_44 .. :try_end_50} :catchall_9b

    .line 183
    :try_start_50
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v1

    const-wide/16 v3, 0x3e8

    div-long/2addr v1, v3

    .line 184
    invoke-static {}, Ljava/util/UUID;->randomUUID()Ljava/util/UUID;

    move-result-object p0

    invoke-virtual {p0}, Ljava/util/UUID;->toString()Ljava/lang/String;

    move-result-object p0

    const-string v3, "-"

    const-string v4, ""

    invoke-virtual {p0, v3, v4}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;

    move-result-object p0

    .line 185
    const-string v3, "ts"

    invoke-virtual {p1, v3, v1, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    .line 186
    const-string v1, "nonce"

    invoke-virtual {p1, v1, p0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 188
    invoke-static {p1}, Lcom/dingtalk/groupbill/net/CryptoBox;->sortedJson(Lorg/json/JSONObject;)Ljava/lang/String;

    move-result-object p0

    .line 189
    const-string v1, "HmacSHA256"

    invoke-static {v1}, Ljavax/crypto/Mac;->getInstance(Ljava/lang/String;)Ljavax/crypto/Mac;

    move-result-object v1

    .line 190
    new-instance v2, Ljavax/crypto/spec/SecretKeySpec;

    const-string v3, "HmacSHA256"

    invoke-direct {v2, v0, v3}, Ljavax/crypto/spec/SecretKeySpec;-><init>([BLjava/lang/String;)V

    invoke-virtual {v1, v2}, Ljavax/crypto/Mac;->init(Ljava/security/Key;)V

    .line 191
    const-string v0, "sig"

    sget-object v2, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p0, v2}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p0

    invoke-virtual {v1, p0}, Ljavax/crypto/Mac;->doFinal([B)[B

    move-result-object p0

    invoke-static {p0}, Lcom/dingtalk/groupbill/net/CryptoBox;->toHex([B)Ljava/lang/String;

    move-result-object p0

    invoke-virtual {p1, v0, p0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    :try_end_98
    .catchall {:try_start_50 .. :try_end_98} :catchall_9e

    .line 194
    goto :goto_9f

    .line 179
    :cond_99
    :goto_99
    :try_start_99
    monitor-exit p0

    return-void

    .line 182
    :catchall_9b
    move-exception p1

    monitor-exit p0
    :try_end_9d
    .catchall {:try_start_99 .. :try_end_9d} :catchall_9b

    :try_start_9d
    throw p1
    :try_end_9e
    .catchall {:try_start_9d .. :try_end_9e} :catchall_9e

    .line 192
    :catchall_9e
    move-exception p0

    .line 195
    :goto_9f
    return-void

    .line 155
    :cond_a0
    :goto_a0
    return-void
.end method

.method private static sortedJson(Lorg/json/JSONObject;)Ljava/lang/String;
    .registers 7
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 370
    new-instance v0, Ljava/util/ArrayList;

    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V

    .line 371
    invoke-virtual {p0}, Lorg/json/JSONObject;->keys()Ljava/util/Iterator;

    move-result-object v1

    .line 372
    :goto_9
    invoke-interface {v1}, Ljava/util/Iterator;->hasNext()Z

    move-result v2

    if-eqz v2, :cond_23

    .line 373
    invoke-interface {v1}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v2

    invoke-static {v2}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v2

    .line 374
    const-string v3, "sig"

    invoke-virtual {v3, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v3

    if-nez v3, :cond_22

    .line 375
    invoke-virtual {v0, v2}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z

    .line 377
    :cond_22
    goto :goto_9

    .line 378
    :cond_23
    invoke-static {v0}, Ljava/util/Collections;->sort(Ljava/util/List;)V

    .line 379
    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "{"

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    .line 380
    const/4 v2, 0x0

    :goto_2e
    invoke-virtual {v0}, Ljava/util/ArrayList;->size()I

    move-result v3

    if-ge v2, v3, :cond_5d

    .line 381
    if-lez v2, :cond_3b

    .line 382
    const/16 v3, 0x2c

    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 384
    :cond_3b
    invoke-virtual {v0, v2}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;

    move-result-object v3

    check-cast v3, Ljava/lang/String;

    .line 385
    invoke-static {v3}, Lorg/json/JSONObject;->quote(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    const/16 v5, 0x3a

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {p0, v3}, Lorg/json/JSONObject;->get(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v3

    invoke-static {v3}, Lcom/dingtalk/groupbill/net/CryptoBox;->jsonValue(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 380
    add-int/lit8 v2, v2, 0x1

    goto :goto_2e

    .line 387
    :cond_5d
    const/16 p0, 0x7d

    invoke-virtual {v1, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 388
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private static toB64([B)Ljava/lang/String;
    .registers 7

    .line 316
    const-string v0, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    invoke-virtual {v0}, Ljava/lang/String;->toCharArray()[C

    move-result-object v0

    .line 317
    new-instance v1, Ljava/lang/StringBuilder;

    array-length v2, p0

    add-int/lit8 v2, v2, 0x2

    div-int/lit8 v2, v2, 0x3

    mul-int/lit8 v2, v2, 0x4

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(I)V

    .line 318
    const/4 v2, 0x0

    .line 319
    :goto_13
    add-int/lit8 v3, v2, 0x2

    array-length v4, p0

    if-ge v3, v4, :cond_54

    .line 320
    aget-byte v4, p0, v2

    and-int/lit16 v4, v4, 0xff

    shl-int/lit8 v4, v4, 0x10

    add-int/lit8 v5, v2, 0x1

    aget-byte v5, p0, v5

    and-int/lit16 v5, v5, 0xff

    shl-int/lit8 v5, v5, 0x8

    or-int/2addr v4, v5

    aget-byte v3, p0, v3

    and-int/lit16 v3, v3, 0xff

    or-int/2addr v3, v4

    .line 321
    ushr-int/lit8 v4, v3, 0x12

    and-int/lit8 v4, v4, 0x3f

    aget-char v4, v0, v4

    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v4

    ushr-int/lit8 v5, v3, 0xc

    and-int/lit8 v5, v5, 0x3f

    aget-char v5, v0, v5

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v4

    ushr-int/lit8 v5, v3, 0x6

    and-int/lit8 v5, v5, 0x3f

    aget-char v5, v0, v5

    .line 322
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v4

    and-int/lit8 v3, v3, 0x3f

    aget-char v3, v0, v3

    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 323
    add-int/lit8 v2, v2, 0x3

    .line 324
    goto :goto_13

    .line 325
    :cond_54
    array-length v3, p0

    if-ge v2, v3, :cond_9b

    .line 326
    aget-byte v3, p0, v2

    and-int/lit16 v3, v3, 0xff

    shl-int/lit8 v3, v3, 0x10

    .line 327
    ushr-int/lit8 v4, v3, 0x12

    and-int/lit8 v4, v4, 0x3f

    aget-char v4, v0, v4

    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 328
    add-int/lit8 v2, v2, 0x1

    array-length v4, p0

    if-ge v2, v4, :cond_8c

    .line 329
    aget-byte p0, p0, v2

    and-int/lit16 p0, p0, 0xff

    shl-int/lit8 p0, p0, 0x8

    or-int/2addr p0, v3

    .line 330
    ushr-int/lit8 v2, p0, 0xc

    and-int/lit8 v2, v2, 0x3f

    aget-char v2, v0, v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v2

    ushr-int/lit8 p0, p0, 0x6

    and-int/lit8 p0, p0, 0x3f

    aget-char p0, v0, p0

    invoke-virtual {v2, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object p0

    const/16 v0, 0x3d

    invoke-virtual {p0, v0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    goto :goto_9b

    .line 332
    :cond_8c
    ushr-int/lit8 p0, v3, 0xc

    and-int/lit8 p0, p0, 0x3f

    aget-char p0, v0, p0

    invoke-virtual {v1, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object p0

    const-string v0, "=="

    invoke-virtual {p0, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 335
    :cond_9b
    :goto_9b
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private static toHex([B)Ljava/lang/String;
    .registers 7

    .line 417
    const-string v0, "0123456789abcdef"

    invoke-virtual {v0}, Ljava/lang/String;->toCharArray()[C

    move-result-object v0

    .line 418
    array-length v1, p0

    mul-int/lit8 v1, v1, 0x2

    new-array v1, v1, [C

    .line 419
    const/4 v2, 0x0

    :goto_c
    array-length v3, p0

    if-ge v2, v3, :cond_26

    .line 420
    aget-byte v3, p0, v2

    and-int/lit16 v3, v3, 0xff

    .line 421
    mul-int/lit8 v4, v2, 0x2

    ushr-int/lit8 v5, v3, 0x4

    aget-char v5, v0, v5

    aput-char v5, v1, v4

    .line 422
    add-int/lit8 v4, v4, 0x1

    and-int/lit8 v3, v3, 0xf

    aget-char v3, v0, v3

    aput-char v3, v1, v4

    .line 419
    add-int/lit8 v2, v2, 0x1

    goto :goto_c

    .line 424
    :cond_26
    new-instance p0, Ljava/lang/String;

    invoke-direct {p0, v1}, Ljava/lang/String;-><init>([C)V

    return-object p0
.end method

.method private static toPem(Ljava/lang/String;[B)Ljava/lang/String;
    .registers 7

    .line 298
    invoke-static {p1}, Lcom/dingtalk/groupbill/net/CryptoBox;->toB64([B)Ljava/lang/String;

    move-result-object p1

    .line 299
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 300
    const-string v1, "-----BEGIN "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v2, "-----\n"

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 301
    const/4 v1, 0x0

    :goto_19
    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v3

    if-ge v1, v3, :cond_34

    .line 302
    add-int/lit8 v3, v1, 0x40

    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v4

    invoke-static {v3, v4}, Ljava/lang/Math;->min(II)I

    move-result v4

    invoke-virtual {v0, p1, v1, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/CharSequence;II)Ljava/lang/StringBuilder;

    move-result-object v1

    const/16 v4, 0xa

    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 301
    move v1, v3

    goto :goto_19

    .line 304
    :cond_34
    const-string p1, "-----END "

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 305
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method
