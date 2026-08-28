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
    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->deviceId:Ljava/lang/String;

    return-void
.end method

.method private constructor <init>()V
    .registers 1

    .line 56
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

    .line 196
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v0

    const-wide/16 v2, 0x3e8

    div-long/2addr v0, v2

    .line 197
    invoke-static {}, Ljava/util/UUID;->randomUUID()Ljava/util/UUID;

    move-result-object v2

    invoke-virtual {v2}, Ljava/util/UUID;->toString()Ljava/lang/String;

    move-result-object v2

    const-string v3, "-"

    const-string v4, ""

    invoke-virtual {v2, v3, v4}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;

    move-result-object v2

    .line 198
    const-string v3, "SHA-256"

    invoke-static {v3}, Ljava/security/MessageDigest;->getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;

    move-result-object v3

    .line 199
    invoke-virtual {v3, p3}, Ljava/security/MessageDigest;->digest([B)[B

    move-result-object p3

    invoke-static {p3}, Lcom/dingtalk/groupbill/net/CryptoBox;->toHex([B)Ljava/lang/String;

    move-result-object p3

    .line 200
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

    .line 201
    const-string p2, "HmacSHA256"

    invoke-static {p2}, Ljavax/crypto/Mac;->getInstance(Ljava/lang/String;)Ljavax/crypto/Mac;

    move-result-object p3

    .line 202
    new-instance v3, Ljavax/crypto/spec/SecretKeySpec;

    sget-object v4, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    invoke-direct {v3, v4, p2}, Ljavax/crypto/spec/SecretKeySpec;-><init>([BLjava/lang/String;)V

    invoke-virtual {p3, v3}, Ljavax/crypto/Mac;->init(Ljava/security/Key;)V

    .line 203
    sget-object p2, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p1, p2}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p1

    invoke-virtual {p3, p1}, Ljavax/crypto/Mac;->doFinal([B)[B

    move-result-object p1

    invoke-static {p1}, Lcom/dingtalk/groupbill/net/CryptoBox;->toHex([B)Ljava/lang/String;

    move-result-object p1

    .line 204
    const-string p2, "X-Device-Id"

    sget-object p3, Lcom/dingtalk/groupbill/net/CryptoBox;->deviceId:Ljava/lang/String;

    invoke-virtual {p0, p2, p3}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 205
    const-string p2, "X-Timestamp"

    invoke-static {v0, v1}, Ljava/lang/String;->valueOf(J)Ljava/lang/String;

    move-result-object p3

    invoke-virtual {p0, p2, p3}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 206
    const-string p2, "X-Nonce"

    invoke-virtual {p0, p2, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 207
    const-string p2, "X-Sign"

    invoke-virtual {p0, p2, p1}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 208
    return-void
.end method

.method private static doEnrollLocked()V
    .registers 7
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 145
    const-string v0, "RSA"

    invoke-static {v0}, Ljava/security/KeyPairGenerator;->getInstance(Ljava/lang/String;)Ljava/security/KeyPairGenerator;

    move-result-object v1

    .line 146
    new-instance v2, Ljava/security/SecureRandom;

    invoke-direct {v2}, Ljava/security/SecureRandom;-><init>()V

    const/16 v3, 0x800

    invoke-virtual {v1, v3, v2}, Ljava/security/KeyPairGenerator;->initialize(ILjava/security/SecureRandom;)V

    .line 147
    invoke-virtual {v1}, Ljava/security/KeyPairGenerator;->generateKeyPair()Ljava/security/KeyPair;

    move-result-object v1

    .line 148
    invoke-virtual {v1}, Ljava/security/KeyPair;->getPrivate()Ljava/security/PrivateKey;

    move-result-object v2

    sput-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->devicePrivateKey:Ljava/security/PrivateKey;

    .line 149
    invoke-virtual {v1}, Ljava/security/KeyPair;->getPublic()Ljava/security/PublicKey;

    move-result-object v1

    invoke-interface {v1}, Ljava/security/PublicKey;->getEncoded()[B

    move-result-object v1

    const-string v2, "PUBLIC KEY"

    invoke-static {v2, v1}, Lcom/dingtalk/groupbill/net/CryptoBox;->toPem(Ljava/lang/String;[B)Ljava/lang/String;

    move-result-object v1

    .line 151
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2}, Lorg/json/JSONObject;-><init>()V

    .line 152
    const-string v3, "userId"

    sget-object v4, Lcom/dingtalk/groupbill/net/CryptoBox;->userId:Ljava/lang/String;

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 153
    const-string v3, "accountId"

    sget-object v4, Lcom/dingtalk/groupbill/net/CryptoBox;->accountId:Ljava/lang/String;

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 154
    const-string v3, "devicePublicKey"

    invoke-virtual {v2, v3, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 155
    const-string v1, "/api/device/enroll"

    invoke-virtual {v2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object v2

    invoke-static {v1, v2}, Lcom/dingtalk/groupbill/net/CryptoBox;->httpPost(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    .line 156
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2, v1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 157
    const/4 v1, -0x1

    const-string v3, "code"

    invoke-virtual {v2, v3, v1}, Lorg/json/JSONObject;->optInt(Ljava/lang/String;I)I

    move-result v1

    if-nez v1, :cond_a1

    .line 160
    const-string v1, "data"

    invoke-virtual {v2, v1}, Lorg/json/JSONObject;->getJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v1

    .line 161
    const-string v2, "device_id"

    invoke-virtual {v1, v2}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    sput-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->deviceId:Ljava/lang/String;

    .line 162
    const-string v2, "enc_hmac_secret"

    invoke-virtual {v1, v2}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    .line 163
    const-string v3, "server_public_key"

    invoke-virtual {v1, v3}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    .line 165
    const-string v3, "RSA/ECB/OAEPPadding"

    invoke-static {v3}, Ljavax/crypto/Cipher;->getInstance(Ljava/lang/String;)Ljavax/crypto/Cipher;

    move-result-object v3

    .line 166
    sget-object v4, Lcom/dingtalk/groupbill/net/CryptoBox;->devicePrivateKey:Ljava/security/PrivateKey;

    sget-object v5, Lcom/dingtalk/groupbill/net/CryptoBox;->OAEP:Ljavax/crypto/spec/OAEPParameterSpec;

    const/4 v6, 0x2

    invoke-virtual {v3, v6, v4, v5}, Ljavax/crypto/Cipher;->init(ILjava/security/Key;Ljava/security/spec/AlgorithmParameterSpec;)V

    .line 167
    invoke-static {v2}, Lcom/dingtalk/groupbill/net/CryptoBox;->fromB64(Ljava/lang/String;)[B

    move-result-object v2

    invoke-virtual {v3, v2}, Ljavax/crypto/Cipher;->doFinal([B)[B

    move-result-object v2

    sput-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    .line 168
    invoke-static {v0}, Ljava/security/KeyFactory;->getInstance(Ljava/lang/String;)Ljava/security/KeyFactory;

    move-result-object v0

    new-instance v2, Ljava/security/spec/X509EncodedKeySpec;

    .line 169
    invoke-static {v1}, Lcom/dingtalk/groupbill/net/CryptoBox;->fromPem(Ljava/lang/String;)[B

    move-result-object v1

    invoke-direct {v2, v1}, Ljava/security/spec/X509EncodedKeySpec;-><init>([B)V

    .line 168
    invoke-virtual {v0, v2}, Ljava/security/KeyFactory;->generatePublic(Ljava/security/spec/KeySpec;)Ljava/security/PublicKey;

    move-result-object v0

    sput-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->serverPublicKey:Ljava/security/PublicKey;

    .line 170
    const/4 v0, 0x1

    sput-boolean v0, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    .line 171
    return-void

    .line 158
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

    .line 174
    const-string v0, "AES"

    invoke-static {v0}, Ljavax/crypto/KeyGenerator;->getInstance(Ljava/lang/String;)Ljavax/crypto/KeyGenerator;

    move-result-object v0

    .line 175
    new-instance v1, Ljava/security/SecureRandom;

    invoke-direct {v1}, Ljava/security/SecureRandom;-><init>()V

    const/16 v2, 0x100

    invoke-virtual {v0, v2, v1}, Ljavax/crypto/KeyGenerator;->init(ILjava/security/SecureRandom;)V

    .line 176
    invoke-virtual {v0}, Ljavax/crypto/KeyGenerator;->generateKey()Ljavax/crypto/SecretKey;

    move-result-object v0

    .line 177
    const/16 v1, 0xc

    new-array v1, v1, [B

    .line 178
    new-instance v2, Ljava/security/SecureRandom;

    invoke-direct {v2}, Ljava/security/SecureRandom;-><init>()V

    invoke-virtual {v2, v1}, Ljava/security/SecureRandom;->nextBytes([B)V

    .line 179
    const-string v2, "AES/GCM/NoPadding"

    invoke-static {v2}, Ljavax/crypto/Cipher;->getInstance(Ljava/lang/String;)Ljavax/crypto/Cipher;

    move-result-object v2

    .line 180
    new-instance v3, Ljavax/crypto/spec/GCMParameterSpec;

    const/16 v4, 0x80

    invoke-direct {v3, v4, v1}, Ljavax/crypto/spec/GCMParameterSpec;-><init>(I[B)V

    const/4 v4, 0x1

    invoke-virtual {v2, v4, v0, v3}, Ljavax/crypto/Cipher;->init(ILjava/security/Key;Ljava/security/spec/AlgorithmParameterSpec;)V

    .line 181
    invoke-virtual {v2, p0}, Ljavax/crypto/Cipher;->doFinal([B)[B

    move-result-object p0

    .line 183
    const-string v2, "RSA/ECB/OAEPPadding"

    invoke-static {v2}, Ljavax/crypto/Cipher;->getInstance(Ljava/lang/String;)Ljavax/crypto/Cipher;

    move-result-object v2

    .line 184
    sget-object v3, Lcom/dingtalk/groupbill/net/CryptoBox;->serverPublicKey:Ljava/security/PublicKey;

    sget-object v5, Lcom/dingtalk/groupbill/net/CryptoBox;->OAEP:Ljavax/crypto/spec/OAEPParameterSpec;

    invoke-virtual {v2, v4, v3, v5}, Ljavax/crypto/Cipher;->init(ILjava/security/Key;Ljava/security/spec/AlgorithmParameterSpec;)V

    .line 185
    invoke-interface {v0}, Ljavax/crypto/SecretKey;->getEncoded()[B

    move-result-object v0

    invoke-virtual {v2, v0}, Ljavax/crypto/Cipher;->doFinal([B)[B

    move-result-object v0

    .line 187
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2}, Lorg/json/JSONObject;-><init>()V

    .line 188
    const-string v3, "ek"

    invoke-static {v0}, Lcom/dingtalk/groupbill/net/CryptoBox;->toB64([B)Ljava/lang/String;

    move-result-object v0

    invoke-virtual {v2, v3, v0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 189
    const-string v0, "iv"

    invoke-static {v1}, Lcom/dingtalk/groupbill/net/CryptoBox;->toB64([B)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v2, v0, v1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 190
    const-string v0, "ct"

    invoke-static {p0}, Lcom/dingtalk/groupbill/net/CryptoBox;->toB64([B)Ljava/lang/String;

    move-result-object p0

    invoke-virtual {v2, v0, p0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 191
    return-object v2
.end method

.method public static ensureEnrolled()V
    .registers 9

    .line 72
    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v0

    .line 73
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

    .line 77
    :cond_10
    :try_start_10
    invoke-static {}, Lcom/dingtalk/groupbill/net/CryptoBox;->doEnrollLocked()V
    :try_end_13
    .catchall {:try_start_10 .. :try_end_13} :catchall_14

    .line 86
    goto :goto_3c

    .line 78
    :catchall_14
    move-exception v1

    .line 80
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

    .line 81
    invoke-virtual {v2, v3, v5}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v2

    new-array v3, v4, [Ljava/lang/Object;

    const-string v4, "CryptoBox enroll FAILED"

    aput-object v4, v3, v7

    aput-object v1, v3, v8

    .line 82
    const/4 v1, 0x0

    invoke-virtual {v2, v1, v3}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;
    :try_end_3a
    .catchall {:try_start_15 .. :try_end_3a} :catchall_3b

    .line 85
    goto :goto_3c

    .line 83
    :catchall_3b
    move-exception v1

    .line 87
    :goto_3c
    :try_start_3c
    monitor-exit v0

    .line 88
    return-void

    .line 74
    :cond_3e
    :goto_3e
    monitor-exit v0

    return-void

    .line 87
    :catchall_40
    move-exception v1

    monitor-exit v0
    :try_end_42
    .catchall {:try_start_3c .. :try_end_42} :catchall_40

    throw v1
.end method

.method private static fromB64(Ljava/lang/String;)[B
    .registers 10

    .line 286
    const-string v0, "[^A-Za-z0-9+/=]"

    const-string v1, ""

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 287
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

    .line 288
    :goto_1e
    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result v2

    div-int/lit8 v2, v2, 0x4

    mul-int/lit8 v2, v2, 0x3

    sub-int/2addr v2, v0

    .line 289
    invoke-static {v2, v1}, Ljava/lang/Math;->max(II)I

    move-result v0

    new-array v2, v0, [B

    .line 290
    const/16 v3, 0x80

    new-array v4, v3, [I

    .line 291
    const/4 v5, 0x0

    :goto_32
    if-ge v5, v3, :cond_3a

    .line 292
    const/4 v6, -0x1

    aput v6, v4, v5

    .line 291
    add-int/lit8 v5, v5, 0x1

    goto :goto_32

    .line 294
    :cond_3a
    nop

    .line 295
    const/4 v3, 0x0

    :goto_3c
    const/16 v5, 0x40

    if-ge v3, v5, :cond_4b

    .line 296
    const-string v5, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    invoke-virtual {v5, v3}, Ljava/lang/String;->charAt(I)C

    move-result v5

    aput v3, v4, v5

    .line 295
    add-int/lit8 v3, v3, 0x1

    goto :goto_3c

    .line 298
    :cond_4b
    nop

    .line 299
    const/4 v3, 0x0

    const/4 v5, 0x0

    :goto_4e
    add-int/lit8 v6, v3, 0x3

    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result v7

    if-ge v6, v7, :cond_a2

    .line 300
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

    .line 301
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

    .line 302
    if-ge v5, v0, :cond_8d

    .line 303
    add-int/lit8 v7, v5, 0x1

    ushr-int/lit8 v8, v6, 0x10

    int-to-byte v8, v8

    aput-byte v8, v2, v5

    move v5, v7

    .line 305
    :cond_8d
    if-ge v5, v0, :cond_97

    .line 306
    add-int/lit8 v7, v5, 0x1

    ushr-int/lit8 v8, v6, 0x8

    int-to-byte v8, v8

    aput-byte v8, v2, v5

    move v5, v7

    .line 308
    :cond_97
    if-ge v5, v0, :cond_9f

    .line 309
    add-int/lit8 v7, v5, 0x1

    int-to-byte v6, v6

    aput-byte v6, v2, v5

    move v5, v7

    .line 299
    :cond_9f
    add-int/lit8 v3, v3, 0x4

    goto :goto_4e

    .line 312
    :cond_a2
    return-object v2
.end method

.method private static fromPem(Ljava/lang/String;)[B
    .registers 3

    .line 256
    const-string v0, "-----BEGIN [A-Z ]+-----"

    const-string v1, ""

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 257
    const-string v0, "-----END [A-Z ]+-----"

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 258
    const-string v0, "\\s"

    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 259
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

    .line 211
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

    .line 212
    new-instance v0, Ljava/net/URL;

    invoke-direct {v0, p0}, Ljava/net/URL;-><init>(Ljava/lang/String;)V

    invoke-virtual {v0}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;

    move-result-object p0

    check-cast p0, Ljava/net/HttpURLConnection;

    .line 213
    const/16 v0, 0x1f40

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setConnectTimeout(I)V

    .line 214
    const/16 v0, 0x2ee0

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setReadTimeout(I)V

    .line 215
    const-string v0, "POST"

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setRequestMethod(Ljava/lang/String;)V

    .line 216
    const/4 v0, 0x1

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setDoOutput(Z)V

    .line 217
    const-string v0, "Content-Type"

    const-string v1, "application/json; charset=utf-8"

    invoke-virtual {p0, v0, v1}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 218
    sget-object v0, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p1, v0}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p1

    .line 219
    array-length v0, p1

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setFixedLengthStreamingMode(I)V

    .line 220
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getOutputStream()Ljava/io/OutputStream;

    move-result-object v0

    .line 221
    invoke-virtual {v0, p1}, Ljava/io/OutputStream;->write([B)V

    .line 222
    invoke-virtual {v0}, Ljava/io/OutputStream;->flush()V

    .line 223
    invoke-virtual {v0}, Ljava/io/OutputStream;->close()V

    .line 224
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

    .line 225
    :goto_62
    invoke-static {p1}, Lcom/dingtalk/groupbill/net/CryptoBox;->readAll(Ljava/io/InputStream;)Ljava/lang/String;

    move-result-object p1

    .line 226
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->disconnect()V

    .line 227
    return-object p1
.end method

.method private static jsonValue(Ljava/lang/Object;)Ljava/lang/String;
    .registers 4
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 339
    if-eqz p0, :cond_5c

    sget-object v0, Lorg/json/JSONObject;->NULL:Ljava/lang/Object;

    if-ne p0, v0, :cond_7

    goto :goto_5c

    .line 342
    :cond_7
    instance-of v0, p0, Lorg/json/JSONObject;

    if-eqz v0, :cond_12

    .line 343
    check-cast p0, Lorg/json/JSONObject;

    invoke-static {p0}, Lcom/dingtalk/groupbill/net/CryptoBox;->sortedJson(Lorg/json/JSONObject;)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 345
    :cond_12
    instance-of v0, p0, Lorg/json/JSONArray;

    if-eqz v0, :cond_45

    .line 346
    check-cast p0, Lorg/json/JSONArray;

    .line 347
    new-instance v0, Ljava/lang/StringBuilder;

    const-string v1, "["

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    .line 348
    const/4 v1, 0x0

    :goto_20
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-ge v1, v2, :cond_3b

    .line 349
    if-lez v1, :cond_2d

    .line 350
    const/16 v2, 0x2c

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 352
    :cond_2d
    invoke-virtual {p0, v1}, Lorg/json/JSONArray;->get(I)Ljava/lang/Object;

    move-result-object v2

    invoke-static {v2}, Lcom/dingtalk/groupbill/net/CryptoBox;->jsonValue(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 348
    add-int/lit8 v1, v1, 0x1

    goto :goto_20

    .line 354
    :cond_3b
    const/16 p0, 0x5d

    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 355
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 357
    :cond_45
    instance-of v0, p0, Ljava/lang/Number;

    if-nez v0, :cond_57

    instance-of v0, p0, Ljava/lang/Boolean;

    if-eqz v0, :cond_4e

    goto :goto_57

    .line 360
    :cond_4e
    invoke-static {p0}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object p0

    invoke-static {p0}, Lorg/json/JSONObject;->quote(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 358
    :cond_57
    :goto_57
    invoke-static {p0}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 340
    :cond_5c
    :goto_5c
    const-string p0, "null"

    return-object p0
.end method

.method public static prepareHttp(Ljava/net/HttpURLConnection;Ljava/lang/String;Lorg/json/JSONObject;)[B
    .registers 6

    .line 96
    invoke-virtual {p2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object v0

    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {v0, v1}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object v0

    .line 98
    :try_start_a
    invoke-static {}, Lcom/dingtalk/groupbill/net/CryptoBox;->ensureEnrolled()V

    .line 99
    sget-object v1, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v1
    :try_end_10
    .catchall {:try_start_a .. :try_end_10} :catchall_41

    .line 100
    :try_start_10
    sget-boolean v2, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    if-eqz v2, :cond_3c

    sget-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    if-eqz v2, :cond_3c

    sget-object v2, Lcom/dingtalk/groupbill/net/CryptoBox;->serverPublicKey:Ljava/security/PublicKey;

    if-nez v2, :cond_1d

    goto :goto_3c

    .line 103
    :cond_1d
    monitor-exit v1
    :try_end_1e
    .catchall {:try_start_10 .. :try_end_1e} :catchall_3e

    .line 104
    :try_start_1e
    invoke-virtual {p2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p2

    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p2, v1}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p2

    invoke-static {p2}, Lcom/dingtalk/groupbill/net/CryptoBox;->encryptHybrid([B)Lorg/json/JSONObject;

    move-result-object p2

    .line 105
    invoke-virtual {p2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p2

    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p2, v1}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p2

    .line 106
    const-string v1, "POST"

    invoke-static {p0, v1, p1, p2}, Lcom/dingtalk/groupbill/net/CryptoBox;->applySignHeaders(Ljava/net/HttpURLConnection;Ljava/lang/String;Ljava/lang/String;[B)V
    :try_end_3b
    .catchall {:try_start_1e .. :try_end_3b} :catchall_41

    .line 107
    return-object p2

    .line 101
    :cond_3c
    :goto_3c
    :try_start_3c
    monitor-exit v1

    return-object v0

    .line 103
    :catchall_3e
    move-exception p0

    monitor-exit v1
    :try_end_40
    .catchall {:try_start_3c .. :try_end_40} :catchall_3e

    :try_start_40
    throw p0
    :try_end_41
    .catchall {:try_start_40 .. :try_end_41} :catchall_41

    .line 108
    :catchall_41
    move-exception p0

    .line 109
    return-object v0
.end method

.method private static readAll(Ljava/io/InputStream;)Ljava/lang/String;
    .registers 5
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 231
    if-nez p0, :cond_5

    .line 232
    const-string p0, ""

    return-object p0

    .line 234
    :cond_5
    new-instance v0, Ljava/io/ByteArrayOutputStream;

    invoke-direct {v0}, Ljava/io/ByteArrayOutputStream;-><init>()V

    .line 235
    const/16 v1, 0x1000

    new-array v1, v1, [B

    .line 237
    :goto_e
    invoke-virtual {p0, v1}, Ljava/io/InputStream;->read([B)I

    move-result v2

    if-lez v2, :cond_19

    .line 238
    const/4 v3, 0x0

    invoke-virtual {v0, v1, v3, v2}, Ljava/io/ByteArrayOutputStream;->write([BII)V

    goto :goto_e

    .line 240
    :cond_19
    invoke-virtual {p0}, Ljava/io/InputStream;->close()V

    .line 241
    new-instance p0, Ljava/lang/String;

    invoke-virtual {v0}, Ljava/io/ByteArrayOutputStream;->toByteArray()[B

    move-result-object v0

    sget-object v1, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-direct {p0, v0, v1}, Ljava/lang/String;-><init>([BLjava/nio/charset/Charset;)V

    return-object p0
.end method

.method public static setIdentity(Ljava/lang/String;Ljava/lang/String;)V
    .registers 4

    .line 59
    if-eqz p0, :cond_24

    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_9

    goto :goto_24

    .line 62
    :cond_9
    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter v0

    .line 63
    :try_start_c
    sget-object v1, Lcom/dingtalk/groupbill/net/CryptoBox;->userId:Ljava/lang/String;

    invoke-virtual {p0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-nez v1, :cond_17

    .line 64
    const/4 v1, 0x0

    sput-boolean v1, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    .line 66
    :cond_17
    sput-object p0, Lcom/dingtalk/groupbill/net/CryptoBox;->userId:Ljava/lang/String;

    .line 67
    if-nez p1, :cond_1d

    const-string p1, ""

    :cond_1d
    sput-object p1, Lcom/dingtalk/groupbill/net/CryptoBox;->accountId:Ljava/lang/String;

    .line 68
    monitor-exit v0

    .line 69
    return-void

    .line 68
    :catchall_21
    move-exception p0

    monitor-exit v0
    :try_end_23
    .catchall {:try_start_c .. :try_end_23} :catchall_21

    throw p0

    .line 60
    :cond_24
    :goto_24
    return-void
.end method

.method public static signWsData(Ljava/lang/String;Lorg/json/JSONObject;)V
    .registers 7

    .line 115
    if-eqz p1, :cond_81

    if-nez p0, :cond_6

    goto/16 :goto_81

    .line 118
    :cond_6
    const-string v0, "bill.upsert"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1f

    const-string v0, "alipay.upload"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1f

    const-string v0, "rpc.result"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p0

    if-nez p0, :cond_1f

    .line 119
    return-void

    .line 122
    :cond_1f
    :try_start_1f
    invoke-static {}, Lcom/dingtalk/groupbill/net/CryptoBox;->ensureEnrolled()V

    .line 124
    sget-object p0, Lcom/dingtalk/groupbill/net/CryptoBox;->LOCK:Ljava/lang/Object;

    monitor-enter p0
    :try_end_25
    .catchall {:try_start_1f .. :try_end_25} :catchall_7f

    .line 125
    :try_start_25
    sget-boolean v0, Lcom/dingtalk/groupbill/net/CryptoBox;->enrolled:Z

    if-eqz v0, :cond_7a

    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    if-nez v0, :cond_2e

    goto :goto_7a

    .line 128
    :cond_2e
    sget-object v0, Lcom/dingtalk/groupbill/net/CryptoBox;->hmacSecret:[B

    .line 129
    monitor-exit p0
    :try_end_31
    .catchall {:try_start_25 .. :try_end_31} :catchall_7c

    .line 130
    :try_start_31
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v1

    const-wide/16 v3, 0x3e8

    div-long/2addr v1, v3

    .line 131
    invoke-static {}, Ljava/util/UUID;->randomUUID()Ljava/util/UUID;

    move-result-object p0

    invoke-virtual {p0}, Ljava/util/UUID;->toString()Ljava/lang/String;

    move-result-object p0

    const-string v3, "-"

    const-string v4, ""

    invoke-virtual {p0, v3, v4}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;

    move-result-object p0

    .line 132
    const-string v3, "ts"

    invoke-virtual {p1, v3, v1, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;J)Lorg/json/JSONObject;

    .line 133
    const-string v1, "nonce"

    invoke-virtual {p1, v1, p0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 135
    invoke-static {p1}, Lcom/dingtalk/groupbill/net/CryptoBox;->sortedJson(Lorg/json/JSONObject;)Ljava/lang/String;

    move-result-object p0

    .line 136
    const-string v1, "HmacSHA256"

    invoke-static {v1}, Ljavax/crypto/Mac;->getInstance(Ljava/lang/String;)Ljavax/crypto/Mac;

    move-result-object v1

    .line 137
    new-instance v2, Ljavax/crypto/spec/SecretKeySpec;

    const-string v3, "HmacSHA256"

    invoke-direct {v2, v0, v3}, Ljavax/crypto/spec/SecretKeySpec;-><init>([BLjava/lang/String;)V

    invoke-virtual {v1, v2}, Ljavax/crypto/Mac;->init(Ljava/security/Key;)V

    .line 138
    const-string v0, "sig"

    sget-object v2, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;

    invoke-virtual {p0, v2}, Ljava/lang/String;->getBytes(Ljava/nio/charset/Charset;)[B

    move-result-object p0

    invoke-virtual {v1, p0}, Ljavax/crypto/Mac;->doFinal([B)[B

    move-result-object p0

    invoke-static {p0}, Lcom/dingtalk/groupbill/net/CryptoBox;->toHex([B)Ljava/lang/String;

    move-result-object p0

    invoke-virtual {p1, v0, p0}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    :try_end_79
    .catchall {:try_start_31 .. :try_end_79} :catchall_7f

    .line 141
    goto :goto_80

    .line 126
    :cond_7a
    :goto_7a
    :try_start_7a
    monitor-exit p0

    return-void

    .line 129
    :catchall_7c
    move-exception p1

    monitor-exit p0
    :try_end_7e
    .catchall {:try_start_7a .. :try_end_7e} :catchall_7c

    :try_start_7e
    throw p1
    :try_end_7f
    .catchall {:try_start_7e .. :try_end_7f} :catchall_7f

    .line 139
    :catchall_7f
    move-exception p0

    .line 142
    :goto_80
    return-void

    .line 116
    :cond_81
    :goto_81
    return-void
.end method

.method private static sortedJson(Lorg/json/JSONObject;)Ljava/lang/String;
    .registers 7
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 317
    new-instance v0, Ljava/util/ArrayList;

    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V

    .line 318
    invoke-virtual {p0}, Lorg/json/JSONObject;->keys()Ljava/util/Iterator;

    move-result-object v1

    .line 319
    :goto_9
    invoke-interface {v1}, Ljava/util/Iterator;->hasNext()Z

    move-result v2

    if-eqz v2, :cond_23

    .line 320
    invoke-interface {v1}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v2

    invoke-static {v2}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v2

    .line 321
    const-string v3, "sig"

    invoke-virtual {v3, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v3

    if-nez v3, :cond_22

    .line 322
    invoke-virtual {v0, v2}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z

    .line 324
    :cond_22
    goto :goto_9

    .line 325
    :cond_23
    invoke-static {v0}, Ljava/util/Collections;->sort(Ljava/util/List;)V

    .line 326
    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "{"

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    .line 327
    const/4 v2, 0x0

    :goto_2e
    invoke-virtual {v0}, Ljava/util/ArrayList;->size()I

    move-result v3

    if-ge v2, v3, :cond_5d

    .line 328
    if-lez v2, :cond_3b

    .line 329
    const/16 v3, 0x2c

    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 331
    :cond_3b
    invoke-virtual {v0, v2}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;

    move-result-object v3

    check-cast v3, Ljava/lang/String;

    .line 332
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

    .line 327
    add-int/lit8 v2, v2, 0x1

    goto :goto_2e

    .line 334
    :cond_5d
    const/16 p0, 0x7d

    invoke-virtual {v1, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 335
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private static toB64([B)Ljava/lang/String;
    .registers 7

    .line 263
    const-string v0, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    invoke-virtual {v0}, Ljava/lang/String;->toCharArray()[C

    move-result-object v0

    .line 264
    new-instance v1, Ljava/lang/StringBuilder;

    array-length v2, p0

    add-int/lit8 v2, v2, 0x2

    div-int/lit8 v2, v2, 0x3

    mul-int/lit8 v2, v2, 0x4

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(I)V

    .line 265
    const/4 v2, 0x0

    .line 266
    :goto_13
    add-int/lit8 v3, v2, 0x2

    array-length v4, p0

    if-ge v3, v4, :cond_54

    .line 267
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

    .line 268
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

    .line 269
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v4

    and-int/lit8 v3, v3, 0x3f

    aget-char v3, v0, v3

    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 270
    add-int/lit8 v2, v2, 0x3

    .line 271
    goto :goto_13

    .line 272
    :cond_54
    array-length v3, p0

    if-ge v2, v3, :cond_9b

    .line 273
    aget-byte v3, p0, v2

    and-int/lit16 v3, v3, 0xff

    shl-int/lit8 v3, v3, 0x10

    .line 274
    ushr-int/lit8 v4, v3, 0x12

    and-int/lit8 v4, v4, 0x3f

    aget-char v4, v0, v4

    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 275
    add-int/lit8 v2, v2, 0x1

    array-length v4, p0

    if-ge v2, v4, :cond_8c

    .line 276
    aget-byte p0, p0, v2

    and-int/lit16 p0, p0, 0xff

    shl-int/lit8 p0, p0, 0x8

    or-int/2addr p0, v3

    .line 277
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

    .line 279
    :cond_8c
    ushr-int/lit8 p0, v3, 0xc

    and-int/lit8 p0, p0, 0x3f

    aget-char p0, v0, p0

    invoke-virtual {v1, p0}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object p0

    const-string v0, "=="

    invoke-virtual {p0, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 282
    :cond_9b
    :goto_9b
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private static toHex([B)Ljava/lang/String;
    .registers 7

    .line 364
    const-string v0, "0123456789abcdef"

    invoke-virtual {v0}, Ljava/lang/String;->toCharArray()[C

    move-result-object v0

    .line 365
    array-length v1, p0

    mul-int/lit8 v1, v1, 0x2

    new-array v1, v1, [C

    .line 366
    const/4 v2, 0x0

    :goto_c
    array-length v3, p0

    if-ge v2, v3, :cond_26

    .line 367
    aget-byte v3, p0, v2

    and-int/lit16 v3, v3, 0xff

    .line 368
    mul-int/lit8 v4, v2, 0x2

    ushr-int/lit8 v5, v3, 0x4

    aget-char v5, v0, v5

    aput-char v5, v1, v4

    .line 369
    add-int/lit8 v4, v4, 0x1

    and-int/lit8 v3, v3, 0xf

    aget-char v3, v0, v3

    aput-char v3, v1, v4

    .line 366
    add-int/lit8 v2, v2, 0x1

    goto :goto_c

    .line 371
    :cond_26
    new-instance p0, Ljava/lang/String;

    invoke-direct {p0, v1}, Ljava/lang/String;-><init>([C)V

    return-object p0
.end method

.method private static toPem(Ljava/lang/String;[B)Ljava/lang/String;
    .registers 7

    .line 245
    invoke-static {p1}, Lcom/dingtalk/groupbill/net/CryptoBox;->toB64([B)Ljava/lang/String;

    move-result-object p1

    .line 246
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 247
    const-string v1, "-----BEGIN "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v2, "-----\n"

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 248
    const/4 v1, 0x0

    :goto_19
    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v3

    if-ge v1, v3, :cond_34

    .line 249
    add-int/lit8 v3, v1, 0x40

    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v4

    invoke-static {v3, v4}, Ljava/lang/Math;->min(II)I

    move-result v4

    invoke-virtual {v0, p1, v1, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/CharSequence;II)Ljava/lang/StringBuilder;

    move-result-object v1

    const/16 v4, 0xa

    invoke-virtual {v1, v4}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 248
    move v1, v3

    goto :goto_19

    .line 251
    :cond_34
    const-string p1, "-----END "

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 252
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method
