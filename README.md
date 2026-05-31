<p align="center">
  <strong>将 AI 生成的网页代码一键打包为 Android APK 应用</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Android-34-3DDC84?style=flat-square&logo=android&logoColor=white" alt="Android" />
  <img src="https://img.shields.io/badge/JDK-17-ED8B00?style=flat-square&logo=openjdk&logoColor=white" alt="JDK" />
  <img src="https://img.shields.io/badge/Gradle-8.9-02303A?style=flat-square&logo=gradle&logoColor=white" alt="Gradle" />
  <img src="https://img.shields.io/badge/版本-2.3.0-00f0ff?style=flat-square" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License" />
</p>

## Star History

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=sdlw7757/app2apk&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=sdlw7757/app2apk&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=sdlw7757/app2apk&type=Date" width="80%" />
  </picture>
</p>

---

> **⚠️ 重要提示：构建工具链已从仓库中移除**
>
> 为减小仓库体积，`tools/jdk/`、`tools/gradle-8.9/`、`tools/android-sdk/` 等大型构建工具已不再包含在代码仓库中。
>
> **首次运行 `启动服务器.bat` 并提交构建任务时，服务器会自动检测并下载所需工具链（约 3-5GB），下载源为国内镜像（华为云、腾讯云、阿里云等多路备用）。**
>
> 下载完成后，工具将自动放置到 `tools/` 目录下，后续使用无需重复下载。

## 概述

**APP2APK** 是一个专为 AI 编程时代打造的工具。它可以将 ChatGPT、Gemini、DeepSeek、Claude 等 AI 生成的 HTML/JS 代码，通过本地构建流水线，一键打包为原生的 Android APK 安装包。

无论你是 AI 开发者、原型设计师，还是希望快速将 Web 创意变为移动应用，APP2APK 都能让你在 **60 秒内** 完成从代码到 APK 的全流程。

> 首次使用需下载 JDK 17、Gradle 8.9 和 Android SDK 34 工具链（参考上方提示），下载后即可离线使用。

---

## 特性

- **一键构建** — 粘贴代码，填写应用信息，点击构建，自动生成 APK
- **零配置** — 自动下载完整 Android 编译工具链（JDK + Gradle + SDK）
- **实时进度** — SSE 事件流推送构建日志，Web 界面实时展示编译过程
- **WebView 渲染** — 使用 Android WebView 作为运行时容器，兼容性极佳
- **自定义图标** — 支持上传 Base64 编码的 PNG 图标
- **权限管理** — 自由声明 Android 权限（网络、存储、相机等）
- **纯文本支持** — 自动将纯文本/代码包装为 HTML 页面
- **离线可用** — 所有依赖工具本地缓存，无需联网编译
- **响应式 UI** — 赛博朋克风格蓝图界面，支持移动端访问

---

## 项目结构

```
app2apk/
├── server.py                          # 主服务程序 (Python HTTP Server)
├── index.html                         # Web 管理界面 (赛博朋克风格)
├── APP2APK-Builder.spec               # PyInstaller 打包配置
├── .gitignore                         # Git 忽略规则
│
├── android-template/                  # Android 原生项目模板
│   ├── build.gradle                   # 根项目 Gradle 配置
│   ├── settings.gradle                # 项目模块声明 (含阿里云镜像)
│   ├── gradle.properties              # Gradle 属性配置
│   └── app/
│       ├── build.gradle               # 应用模块构建配置
│       └── src/
│           └── main/
│               ├── AndroidManifest.xml # Android 清单文件
│               ├── java/
│               │   └── com/
│               │       └── app2apk/
│               │           └── MainActivity.java  # WebView 主入口
│               └── res/
│                   └── values/
│                       ├── strings.xml # 字符串资源
│                       └── themes.xml  # 主题配置
│
├── builds/                            # 构建输出目录 (运行时生成)
│   ├── A2A-xxxxxxxx/                  # 每个构建任务独立文件夹
│   │   ├── app/build/outputs/apk/     # APK 产物
│   │   └── ...                        # Gradle 中间产物
│   ├── *.apk                          # 构建完成的 APK 文件
│   └── *.log                          # 构建日志文件
│
└── tools/                             # 工具链目录（首次构建自动下载）
    ├── jdk/                           # [自动下载] JDK 17
    ├── gradle-8.9/                    # [自动下载] Gradle 8.9
    └── android-sdk/                   # [自动下载] Android SDK 34
```

---

## 工作原理

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  用户粘贴     │      │  Python 服务器 │      │  Gradle 构建  │      │  APK 输出     │
│  HTML/JS 代码  │ ──→  │  (server.py)  │ ──→  │  编译流水线    │ ──→  │  安装包       │
│              │      │              │      │              │      │              │
│  ● 应用名称   │      │  1. 生成项目   │      │  assemble     │      │  app-debug   │
│  ● 版本号     │      │  2. 写入代码   │      │  Debug        │      │  .apk        │
│  ● 权限声明   │      │  3. 配置清单   │      │              │      │              │
│  ● 图标       │      │  4. 调用 Gradle│      │  JDK 17       │      │  即时下载    │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
```

核心流程：

1. **用户通过 Web 界面** 提交 HTML/JS 代码、应用名称、版本、权限和图标
2. **Python 服务器** 接收请求，创建唯一任务 ID，将代码写入 Android 项目模板
3. **服务器自动查找或下载** JDK 17、Gradle 8.9、Android SDK 34（工具链自动下载）
4. **Gradle 编译流水线** 执行 `assembleDebug`，将 Web 代码编译为 APK
5. **构建完成后** 用户可通过浏览器直接下载 APK 安装包

---

## 快速开始

### 前置条件

- Python 3.10+
- Windows / macOS / Linux
- 4GB+ 可用内存（Gradle 构建需要）
- 10GB+ 磁盘空间（含工具链）

### 启动服务

```bash
# 克隆项目
git clone <repository-url>
cd demo2apk

# 双击运行 启动服务器.bat 或在终端执行：
启动服务器.bat
```

服务启动后，浏览器将自动打开管理界面。

> **提示**：首次运行时会自动检测并下载工具链（参考页面顶部的 ⚠️ 提示）。下载完成后，服务器会自动检测 `tools/` 目录下的 JDK、Gradle 和 Android SDK。

### 访问地址

| 接口 | 地址 | 说明 |
|------|------|------|
| Web 管理界面 | http://localhost:8080 | 可视化构建 APK |
| 工具状态接口 | http://localhost:8080/api/tools/status | 查看工具链状态 |
| 构建 API | http://localhost:8080/api/build | 提交构建任务 |

---

## API 文档

### 提交构建任务

```http
POST /api/build
Content-Type: application/json

{
  "mode": "html",
  "appName": "我的应用",
  "version": "1.0.0",
  "code": "<!DOCTYPE html>...",
  "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"],
  "icon": "base64_encoded_png_data"
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `mode` | string | 否 | `"html"` | `"html"` 或 `"js"` |
| `appName` | string | 否 | `"App"` | Android 应用名称 |
| `version` | string | 否 | `"1.0.0"` | 版本号 |
| `code` | string | 是 | - | HTML/JS 代码内容 |
| `permissions` | array | 否 | `["INTERNET","ACCESS_NETWORK_STATE"]` | Android 权限列表 |
| `icon` | string | 否 | null | Base64 编码的 PNG 图标 |

**响应：**

```json
{
  "taskId": "A2A-558992E7",
  "status": "queued"
}
```

### 查询构建状态

```http
GET /api/build/{taskId}/status
```

**响应：**

```json
{
  "taskId": "A2A-558992E7",
  "status": "building",
  "progress": 45,
  "logs": ["[BUILD] ..."],
  "apkReady": false
}
```

### 下载 APK

```http
GET /api/build/{taskId}/download
```

### SSE 实时日志流

```http
GET /api/build/{taskId}/stream
```

返回 `text/event-stream` 格式的实时构建日志推送。

### 查看工具链状态

```http
GET /api/tools/status
```

**响应：**

```json
{
  "java": true,
  "gradle": true,
  "androidSdk": true,
  "version": "2.3.0"
}
```

---

## Android 模板说明

生成的 APK 基于以下技术栈：

- **容器**：Android WebView（支持 JavaScript、DOM 存储、文件访问）
- **最低 SDK**：Android 7.0 (API 24)
- **目标 SDK**：Android 14 (API 34)
- **Java 版本**：Java 17
- **启动页**：Android SplashScreen API
- **返回键**：支持 WebView 内历史导航

模板位于 [android-template](android-template) 目录，你可以根据需求修改：

- `build.gradle` — 调整编译 SDK 版本、依赖库
- `AndroidManifest.xml` — 添加 Activity、Service、权限
- `MainActivity.java` — 定制 WebView 行为（JavaScript 接口、导航等）

---

## 使用 PyInstaller 打包

项目提供了 [APP2APK-Builder.spec](APP2APK-Builder.spec) 文件，可将 server.py 和 index.html 打包为独立的 Windows 可执行文件：

```bash
pip install pyinstaller
pyinstaller APP2APK-Builder.spec
```

打包后，将生成的 `APP2APK-Builder.exe` 放置在包含 `tools/` 目录（含已下载的工具链）的文件夹中即可运行。

---

## 技术细节

### 工具链自动发现

服务器按以下优先级查找编译工具：

1. **环境变量**：`JAVA_HOME`、`GRADLE_HOME`、`ANDROID_HOME` / `ANDROID_SDK_ROOT`
2. **内置目录**：`tools/jdk/`、`tools/gradle-8.9/`、`tools/android-sdk/`（需提前下载）
3. **系统路径**：常见 JDK 安装位置（如 `C:\Program Files\Java\`）
4. **自动下载**：如未找到，从国内镜像自动下载（华为云、腾讯云、阿里云等多路备用）

### 构建优化

- Gradle 守护进程仅在构建期间运行（`--no-daemon`）
- JVM 分配 2GB 内存（`-Xmx2g`）
- APK 中不压缩 HTML/JS/CSS 等资源文件
- 使用阿里云 Maven 镜像加速依赖下载

---

## 常见问题

**Q：构建失败怎么办？**

A：检查构建日志页面（SSE 流），常见原因包括：代码语法错误、权限不足、磁盘空间不足。你也可以查看 `builds/*.log` 文件获取完整日志。

**Q：如何添加更多 Android 权限？**

A：在 Web 界面的权限列表中勾选所需权限，或在 API 请求的 `permissions` 数组中添加。支持所有标准 Android 权限名。

**Q：支持 iOS 吗？**

A：不支持。本项目专注于 Android APK 构建。iOS 需要 Xcode 和 Apple 开发者账号，不在本项目的范围内。

**Q：如何修改应用图标？**

A：在 Web 界面上传 Base64 编码的 PNG 图片（建议 72×72 或更大），或直接替换模板中的 `mipmap-hdpi/ic_launcher.png`。

---

---

## 赞助支持

如果这个项目对你有帮助，欢迎请作者喝杯咖啡 ☕

<p align="center">
  <table>
    <tr>
      <td align="center">
        <strong>微信赞赏</strong><br>
        <img src="android-template/wechat-qr.png" width="200" alt="微信赞赏码" />
      </td>
      <td align="center">
        <strong>支付宝赞赏</strong><br>
        <img src="android-template/alipay-qr.jpg" width="200" alt="支付宝赞赏码" />
      </td>
    </tr>
  </table>
</p>

你的支持是这个项目持续改进的最大动力！

---

## 开源协议

本项目基于 **MIT License** 开源，你可以自由地使用、修改和分发，只需保留原始版权声明。

```
MIT License

Copyright (c) 2025 APP2APK

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  用 ❤️ 与 AI 打造 &nbsp;|&nbsp; 
  <a href="http://localhost:8080">立即构建你的第一个 APK</a>
</p>
