# APP2APK 模板 ProGuard 规则（debug 构建默认不启用 minify）
# 保留 WebView 相关类
-keep class android.webkit.** { *; }