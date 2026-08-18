setImmediate(function () {
  Java.perform(function () {
    const HttpReporter = Java.use("com.dingtalk.groupbill.net.HttpReporter");
    const baseUrl = String(HttpReporter.baseUrl());
    if (baseUrl !== "http://127.0.0.1:18722") {
      throw new Error("unexpected baseUrl: " + baseUrl);
    }
    HttpReporter.uploadOrder(
      "local-debug-user",
      "local-debug-order",
      "local-debug-pay",
      1.0
    );
    console.log("frida-http-smoke-dispatched");
  });
});
