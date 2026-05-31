#!/usr/bin/env python3
import os, sys, json, zipfile, io, shutil, uuid, time, threading, webbrowser, re, subprocess, urllib.request, tarfile, tempfile, html as htmlmod, base64, struct, ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

APP2APK_VERSION = "2.3.0"
if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
    BASE_DIR = getattr(sys, '_MEIPASS', EXE_DIR)
    TOOLS_DIR = os.path.join(EXE_DIR, "tools")
    BUILDS_DIR = os.path.join(EXE_DIR, "builds")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TOOLS_DIR = os.path.join(BASE_DIR, "tools")
    BUILDS_DIR = os.path.join(BASE_DIR, "builds")
TEMPLATE_DIR = os.path.join(BASE_DIR, "android-template")
GRADLE_URLS = [
    "https://mirrors.huaweicloud.com/gradle/gradle-8.9-bin.zip",
    "https://mirrors.cloud.tencent.com/gradle/gradle-8.9-bin.zip",
    "https://mirrors.aliyun.com/gradle/distributions/gradle-8.9-bin.zip",
    "https://github.com/gradle/gradle/releases/download/v8.9.0/gradle-8.9-bin.zip",
    "https://services.gradle.org/distributions/gradle-8.9-bin.zip"
]
JAVA_URLS = [
    "https://mirrors.huaweicloud.com/openjdk/17/openjdk-17_windows-x64_bin.zip",
    "https://mirrors.tencent.com/openjdk/17/openjdk-17_windows-x64_bin.zip",
    "https://aka.ms/download-jdk/microsoft-jdk-17-windows-x64.zip",
    "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse"
]
SDK_CMDLINE_URLS = [
    "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip",
    "https://mirrors.huaweicloud.com/android/repository/commandlinetools-win-11076708_latest.zip",
    "https://mirrors.tencent.com/android/repository/commandlinetools-win-11076708_latest.zip"
]
SDK_LICENSES_URL = "https://dl.google.com/android/repository/repository3-2.xml"

build_tasks = {}
build_logs_lock = threading.Lock()

def log(msg):
    print(f"[APP2APK] {msg}")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def download_file(url, dest, desc="Downloading", task_id=None):
    log(f"{desc}: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            last_pct = -1
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0 and task_id:
                        pct = int(downloaded * 100 / total)
                        if pct // 5 != last_pct // 5 or pct == 100:
                            last_pct = pct
                            append_log(task_id, f"[TOOLS] {desc}: {pct}% ({downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB)")
        log(f"Downloaded to {dest} ({downloaded} bytes)")
        return True
    except Exception as e:
        msg = f"Download failed: {url} - {e}"
        log(msg)
        if task_id:
            append_log(task_id, f"[TOOLS] {desc} download failed, trying next mirror...")
        return False

def extract_zip(zip_path, extract_to):
    log(f"Extracting {zip_path} to {extract_to}")
    ensure_dir(extract_to)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    log("Extraction done")

def extract_tar_gz(tar_path, extract_to):
    log(f"Extracting {tar_path} to {extract_to}")
    ensure_dir(extract_to)
    with tarfile.open(tar_path, "r:gz") as tf:
        tf.extractall(extract_to)
    log("Extraction done")

def find_java_home():
    java_home = os.environ.get("JAVA_HOME")
    if java_home and os.path.isfile(os.path.join(java_home, "bin", "java.exe")):
        return java_home
    java_home_dirs = [
        os.path.join(TOOLS_DIR, "jdk"),
        r"C:\Program Files\Java\jdk-17",
        r"C:\Program Files\Eclipse Adoptium\jdk-17.0.12.7-hotspot",
    ]
    for d in java_home_dirs:
        if os.path.isfile(os.path.join(d, "bin", "java.exe")):
            return d
    return None

def find_gradle_home():
    gradle_home = os.environ.get("GRADLE_HOME")
    if gradle_home and os.path.isfile(os.path.join(gradle_home, "bin", "gradle.bat")):
        return gradle_home
    gradle_dir = os.path.join(TOOLS_DIR, "gradle-8.9")
    if os.path.isfile(os.path.join(gradle_dir, "bin", "gradle.bat")):
        return gradle_dir
    return None

def find_android_sdk():
    sdk_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk_home and os.path.isdir(os.path.join(sdk_home, "platforms")):
        return sdk_home
    sdk_dir = os.path.join(TOOLS_DIR, "android-sdk")
    if os.path.isdir(os.path.join(sdk_dir, "platforms")):
        return sdk_dir
    return None

def ensure_java(task_id=None):
    jh = find_java_home()
    if jh:
        log(f"Java found at: {jh}")
        if task_id:
            append_log(task_id, "[TOOLS] JDK 17 found")
        return jh
    log("Java not found, downloading JDK 17...")
    if task_id:
        append_log(task_id, "[TOOLS] JDK 17 not found, downloading (约 300MB)...")
    jdk_dir = os.path.join(TOOLS_DIR, "jdk")
    ensure_dir(jdk_dir)
    zip_path = os.path.join(TOOLS_DIR, "jdk.zip")
    for url in JAVA_URLS:
        if download_file(url, zip_path, "JDK 17", task_id):
            break
    if os.path.getsize(zip_path) == 0:
        raise Exception("Failed to download JDK")
    if task_id:
        append_log(task_id, "[TOOLS] JDK 17 downloaded, extracting...")
    extract_zip(zip_path, jdk_dir)
    os.remove(zip_path)
    subdirs = [d for d in os.listdir(jdk_dir) if os.path.isdir(os.path.join(jdk_dir, d))]
    if subdirs:
        inner = os.path.join(jdk_dir, subdirs[0])
        for item in os.listdir(inner):
            shutil.move(os.path.join(inner, item), os.path.join(jdk_dir, item))
        os.rmdir(inner)
    jh = find_java_home()
    if not jh:
        raise Exception("Failed to setup JDK")
    log(f"JDK setup at: {jh}")
    if task_id:
        append_log(task_id, "[TOOLS] JDK 17 ready")
    return jh

def ensure_gradle(task_id=None):
    gh = find_gradle_home()
    if gh:
        log(f"Gradle found at: {gh}")
        if task_id:
            append_log(task_id, "[TOOLS] Gradle 8.9 found")
        return gh
    log("Gradle not found, downloading Gradle 8.9...")
    if task_id:
        append_log(task_id, "[TOOLS] Gradle 8.9 not found, downloading (约 150MB)...")
    ensure_dir(TOOLS_DIR)
    zip_path = os.path.join(TOOLS_DIR, "gradle-8.9-bin.zip")
    ok = False
    for url in GRADLE_URLS:
        if download_file(url, zip_path, "Gradle 8.9", task_id):
            ok = True
            break
    if not ok:
        raise Exception("Failed to download Gradle from all mirrors")
    if task_id:
        append_log(task_id, "[TOOLS] Gradle 8.9 downloaded, extracting...")
    extract_zip(zip_path, TOOLS_DIR)
    os.remove(zip_path)
    gh = find_gradle_home()
    if not gh:
        raise Exception("Failed to setup Gradle")
    log(f"Gradle setup at: {gh}")
    if task_id:
        append_log(task_id, "[TOOLS] Gradle 8.9 ready")
    return gh

def ensure_android_sdk(task_id=None):
    sdk = find_android_sdk()
    if sdk:
        log(f"Android SDK found at: {sdk}")
        if task_id:
            append_log(task_id, "[TOOLS] Android SDK 34 found")
        return sdk
    log("Android SDK not found, downloading...")
    if task_id:
        append_log(task_id, "[TOOLS] Android SDK not found, downloading (约 1.5GB)...")
    sdk_dir = os.path.join(TOOLS_DIR, "android-sdk")
    ensure_dir(sdk_dir)
    zip_path = os.path.join(TOOLS_DIR, "cmdline-tools.zip")
    ok = False
    for url in SDK_CMDLINE_URLS:
        if download_file(url, zip_path, "Android SDK", task_id):
            ok = True
            break
    if not ok:
        raise Exception("Failed to download Android SDK from all mirrors")
    cmdline_latest = os.path.join(sdk_dir, "cmdline-tools", "latest")
    ensure_dir(cmdline_latest)
    extract_zip(zip_path, cmdline_latest)
    os.remove(zip_path)
    nested = os.path.join(cmdline_latest, "cmdline-tools")
    if os.path.isdir(nested):
        for item in os.listdir(nested):
            src = os.path.join(nested, item)
            dst = os.path.join(cmdline_latest, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        shutil.rmtree(nested, ignore_errors=True)
    sdkmanager = os.path.join(cmdline_latest, "bin", "sdkmanager.bat") if os.name == "nt" else os.path.join(cmdline_latest, "bin", "sdkmanager")
    if os.path.isfile(sdkmanager):
        log("Installing Android SDK platforms...")
        if task_id:
            append_log(task_id, "[TOOLS] Installing Android platform 34 & build-tools...")
        try:
            jh = find_java_home()
            env = os.environ.copy()
            if jh:
                env["JAVA_HOME"] = jh
            subprocess.run(
                [sdkmanager, "--sdk_root=" + sdk_dir, "--install", "platforms;android-34", "build-tools;34.0.0"],
                input=b"y\n" * 10, capture_output=True, timeout=600, env=env
            )
        except Exception as e:
            log(f"SDK install warning: {e}")
    sdk = find_android_sdk()
    if not sdk:
        sdk = sdk_dir
    if task_id:
        append_log(task_id, "[TOOLS] Android SDK 34 ready")
    return sdk

def get_unique_task_id():
    return "A2A-" + uuid.uuid4().hex[:8].upper()

def copy_template(build_dir):
    if os.path.isdir(TEMPLATE_DIR):
        for item in os.listdir(TEMPLATE_DIR):
            s = os.path.join(TEMPLATE_DIR, item)
            d = os.path.join(build_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

def write_user_code(build_dir, app_name, code_content, is_html=True):
    www_dir = os.path.join(build_dir, "app", "src", "main", "assets", "www")
    ensure_dir(www_dir)
    index_path = os.path.join(www_dir, "index.html")
    is_actually_html = is_html and (code_content.strip().startswith("<!") or code_content.strip().startswith("<html") or code_content.strip().startswith("<"))
    if is_actually_html:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(code_content)
    else:
        html_wrapper = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{htmlmod.escape(app_name)}</title>
<style>
body {{ background:#1a1a2e; color:#e0e0e0; font-family:sans-serif; padding:20px; margin:0; white-space:pre-wrap; word-wrap:break-word; }}
</style>
</head>
<body>
{htmlmod.escape(code_content)}
</body>
</html>"""
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_wrapper)

def write_metadata(build_dir, task_id, app_name, version, file_name):
    strings_path = os.path.join(build_dir, "app", "src", "main", "res", "values", "strings.xml")
    if os.path.isfile(strings_path):
        with open(strings_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(
            r'<string name="app_name">[^<]*</string>',
            f'<string name="app_name">{htmlmod.escape(app_name or "App2Apk")}</string>',
            content
        )
        with open(strings_path, "w", encoding="utf-8") as f:
            f.write(content)
    gradle_path = os.path.join(build_dir, "app", "build.gradle")
    if os.path.isfile(gradle_path):
        with open(gradle_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'versionName\s+"[^"]*"', f'versionName "{version or "1.0.0"}"', content)
        with open(gradle_path, "w", encoding="utf-8") as f:
            f.write(content)

def update_manifest(build_dir, permissions, app_name):
    manifest_path = os.path.join(build_dir, "app", "src", "main", "AndroidManifest.xml")
    if os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'\s*package="[^"]*"', '', content)
        content = re.sub(r'<uses-permission[^>]*/>\s*', '', content)
        perm_xml = "\n".join(f'    <uses-permission android:name="android.permission.{p}" />' for p in permissions)
        content = content.replace("</manifest>", perm_xml + "\n\n</manifest>")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(content)
    pkg_suffix = re.sub(r"[^a-zA-Z0-9]", "", app_name or "app")
    if not pkg_suffix or pkg_suffix[0].isdigit():
        if pkg_suffix:
            pkg_suffix = "app_" + pkg_suffix
        else:
            pkg_suffix = "app"
    pkg_name = "com.app2apk." + pkg_suffix.lower()
    gradle_path = os.path.join(build_dir, "app", "build.gradle")
    if os.path.isfile(gradle_path):
        with open(gradle_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'applicationId\s+"[^"]*"', f'applicationId "{pkg_name}"', content)
        with open(gradle_path, "w", encoding="utf-8") as f:
            f.write(content)

def _make_png(w, h, r, g, b):
    raw = b""
    for y in range(h):
        raw += b"\x00"
        for x in range(w):
            raw += bytes([r, g, b, 255])
    import zlib
    def chunk(ctype, data):
        c = ctype + data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    compressed = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")

def write_app_icon(build_dir, icon_data=None):
    mipmap_dir = os.path.join(build_dir, "app", "src", "main", "res", "mipmap-hdpi")
    ensure_dir(mipmap_dir)
    icon_path = os.path.join(mipmap_dir, "ic_launcher.png")
    if icon_data and len(icon_data) > 100:
        try:
            png_bytes = base64.b64decode(icon_data)
            if png_bytes[:4] == b"\x89PNG":
                with open(icon_path, "wb") as f:
                    f.write(png_bytes)
                return
        except Exception:
            pass
    png = _make_png(72, 72, 0, 180, 255)
    with open(icon_path, "wb") as f:
        f.write(png)

def build_apk(task_id, build_dir, app_name, version, code_content, file_name, permissions, is_html, icon_data=None):
    def build_worker():
        try:
            jh = ensure_java(task_id)
            gh = ensure_gradle(task_id)
            sdk = ensure_android_sdk(task_id)
            append_log(task_id, "[INIT] Build pipeline ready")
            append_log(task_id, f"[INIT] JDK: {jh}")
            append_log(task_id, f"[INIT] Gradle: {gh}")
            append_log(task_id, f"[INIT] Android SDK: {sdk}")
            append_log(task_id, "[SETUP] Creating Android project...")
            copy_template(build_dir)
            write_user_code(build_dir, app_name, code_content, is_html)
            write_metadata(build_dir, task_id, app_name, version, file_name)
            update_manifest(build_dir, permissions, app_name)
            write_app_icon(build_dir, icon_data)
            set_progress(task_id, 10)
            append_log(task_id, "[SETUP] Project structure ready")
            gradle_bin = os.path.join(gh, "bin", "gradle")
            if not os.path.isfile(gradle_bin):
                gradle_bin = os.path.join(gh, "bin", "gradle")
            if os.name == "nt" and not gradle_bin.endswith(".bat"):
                gradle_bin += ".bat"
            env = os.environ.copy()
            env["JAVA_HOME"] = jh
            env["ANDROID_HOME"] = sdk
            env["GRADLE_OPTS"] = "-Dorg.gradle.jvmargs=-Xmx2g"
            apk_output = os.path.join(build_dir, "app", "build", "outputs", "apk", "debug")
            append_log(task_id, "[BUILD] Running Gradle assembleDebug...")
            append_log(task_id, f"[BUILD] Command: {gradle_bin} assembleDebug")
            set_progress(task_id, 20)
            process = subprocess.Popen(
                [gradle_bin, "assembleDebug", "--no-daemon", "--console=plain"],
                cwd=build_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            logs = []
            try:
                for line in iter(process.stdout.readline, ""):
                    line = line.rstrip()
                    if line:
                        logs.append(line)
                        tag = "[BUILD]"
                        if "BUILD SUCCESSFUL" in line:
                            tag = "[DONE]"
                        elif "FAILED" in line.upper() and ("BUILD" in line or "ERROR" in line):
                            tag = "[ERROR]"
                        elif "> Task" in line:
                            tag = "[GRADLE]"
                        append_log(task_id, f"{tag} {line}")
                        pct = min(90, 20 + int(len(logs) * 0.5))
                        set_progress(task_id, pct)
            except Exception as e:
                append_log(task_id, f"[ERROR] Log reading error: {str(e)}")
            process.wait(timeout=600)
            if process.returncode == 0:
                set_progress(task_id, 100)
                append_log(task_id, "[DONE] Build complete! APK generated")
                apk_debug = os.path.join(apk_output, "app-debug.apk")
                if os.path.isfile(apk_debug):
                    final_apk = os.path.join(BUILDS_DIR, f"{task_id}.apk")
                    shutil.copy2(apk_debug, final_apk)
                    append_log(task_id, f"[DONE] APK saved: {final_apk}")
                    build_tasks[task_id]["apk_path"] = final_apk
                build_tasks[task_id]["status"] = "complete"
                build_tasks[task_id]["progress"] = 100
            else:
                set_progress(task_id, 0)
                build_tasks[task_id]["status"] = "error"
                build_tasks[task_id]["error"] = f"Gradle build failed (exit code: {process.returncode})"
                append_log(task_id, f"[ERROR] Gradle build failed (exit code: {process.returncode})")
            log_path = os.path.join(BUILDS_DIR, f"{task_id}.log")
            try:
                with open(log_path, "w", encoding="utf-8") as lf:
                    lf.write(f"APP2APK Build Report\n")
                    lf.write(f"Task: {task_id}\n")
                    lf.write(f"App: {app_name} v{version}\n")
                    lf.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    lf.write(f"Status: {build_tasks[task_id]['status']}\n")
                    lf.write("=" * 60 + "\n")
                    with build_logs_lock:
                        for line in build_tasks[task_id]["logs"]:
                            lf.write(line + "\n")
            except Exception as e:
                append_log(task_id, f"[WARN] Could not save build log: {e}")
        except Exception as e:
            append_log(task_id, f"[ERROR] {str(e)}")
            build_tasks[task_id]["status"] = "error"
            build_tasks[task_id]["error"] = str(e)
            set_progress(task_id, 0)
    t = threading.Thread(target=build_worker, daemon=True)
    t.start()

def append_log(task_id, msg):
    with build_logs_lock:
        if task_id in build_tasks:
            build_tasks[task_id]["logs"].append(msg)

def set_progress(task_id, pct):
    with build_logs_lock:
        if task_id in build_tasks:
            build_tasks[task_id]["progress"] = pct

class App2ApkHandler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._set_cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_file(self, filepath, content_type=None, download_filename=None):
        if not os.path.isfile(filepath):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._set_cors()
            self.end_headers()
            self.wfile.write(b"Not Found")
            return
        if not content_type:
            ext = os.path.splitext(filepath)[1].lower()
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".svg": "image/svg+xml",
                ".apk": "application/vnd.android.package-archive",
            }.get(ext, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self._set_cors()
        if content_type == "application/vnd.android.package-archive":
            filename = download_filename if download_filename else os.path.basename(filepath)
            if not filename.endswith(".apk"):
                filename += ".apk"
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        with open(filepath, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._send_file(os.path.join(BASE_DIR, "index.html"))
        elif path.startswith("/api/build/") and path.endswith("/status"):
            task_id = path.split("/")[3]
            if task_id in build_tasks:
                t = build_tasks[task_id]
                self._send_json({
                    "taskId": task_id,
                    "status": t["status"],
                    "progress": t["progress"],
                    "logs": t["logs"][-50:],
                    "error": t.get("error"),
                    "apkReady": t.get("apk_path") is not None and os.path.isfile(t["apk_path"])
                })
            else:
                self._send_json({"error": "Task not found"}, 404)
        elif path.startswith("/api/build/") and path.endswith("/download"):
            task_id = path.split("/")[3]
            if task_id in build_tasks and build_tasks[task_id].get("apk_path") is not None and os.path.isfile(build_tasks[task_id]["apk_path"]):
                t = build_tasks[task_id]
                self._send_file(t["apk_path"], download_filename=t.get("app_name", ""))
            else:
                self._send_json({"error": "APK not ready"}, 404)
        elif path.startswith("/api/build/") and "/stream" in path:
            task_id = path.split("/")[3]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._set_cors()
            self.end_headers()
            last_logs = 0
            while True:
                with build_logs_lock:
                    if task_id in build_tasks:
                        t = build_tasks[task_id]
                        new_logs = t["logs"][last_logs:]
                        if new_logs:
                            for line in new_logs:
                                self.wfile.write(f"data: {json.dumps({'type': 'log', 'text': line})}\n\n".encode())
                            last_logs = len(t["logs"])
                        self.wfile.write(f"data: {json.dumps({'type': 'progress', 'value': t['progress']})}\n\n".encode())
                        if t["status"] in ("complete", "error"):
                            self.wfile.write(f"data: {json.dumps({'type': 'status', 'status': t['status'], 'taskId': task_id})}\n\n".encode())
                            self.wfile.flush()
                            break
                self.wfile.write(b": heartbeat\n\n")
                self.wfile.flush()
                time.sleep(0.5)
        elif path.startswith("/downloads/"):
            parts = path.split("/")
            filename = parts[2]
            if filename.endswith(".apk"):
                task_id = filename.replace(".apk", "")
                apk_path = os.path.join(BUILDS_DIR, f"{task_id}.apk")
                if os.path.isfile(apk_path):
                    app_name = build_tasks.get(task_id, {}).get("app_name", "")
                    self._send_file(apk_path, download_filename=app_name)
                else:
                    self._send_json({"error": "APK not found"}, 404)
            elif filename.endswith(".log"):
                task_id = filename.replace(".log", "")
                log_path = os.path.join(BUILDS_DIR, f"{task_id}.log")
                if os.path.isfile(log_path):
                    self._send_file(log_path)
                else:
                    self._send_json({"error": "Build log not found"}, 404)
            else:
                self._send_json({"error": "Unknown file type"}, 404)
        elif path == "/api/tools/status":
            self._send_json({
                "java": find_java_home() is not None,
                "gradle": find_gradle_home() is not None,
                "androidSdk": find_android_sdk() is not None,
                "version": APP2APK_VERSION
            })
        else:
            self.send_response(404)
            self._set_cors()
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/build":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            mode = data.get("mode", "html")
            app_name = data.get("appName", "App")
            version = data.get("version", "1.0.0")
            file_name = data.get("fileName", "index.html")
            code_content = data.get("code", "")
            permissions = data.get("permissions", ["INTERNET", "ACCESS_NETWORK_STATE"])
            icon_data = data.get("icon", None)
            is_html = mode != "js"
            task_id = get_unique_task_id()
            build_dir = os.path.join(BUILDS_DIR, task_id)
            ensure_dir(build_dir)
            build_tasks[task_id] = {
                "status": "queued",
                "progress": 0,
                "logs": [f"[QUEUE] Task {task_id} queued", f"[QUEUE] App: {app_name} v{version}"],
                "apk_path": None,
                "app_name": app_name,
            }
            build_apk(task_id, build_dir, app_name, version, code_content, file_name, permissions, is_html, icon_data)
            self._send_json({"taskId": task_id, "status": "queued"})
        else:
            self._send_json({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        pass

def main():
    ensure_dir(BUILDS_DIR)
    port = 8080
    server = HTTPServer(("0.0.0.0", port), App2ApkHandler)
    print(f"""
  ╔══════════════════════════════════════════╗
  ║          APP2APK Build Server            ║
  ║          v{APP2APK_VERSION}                       ║
  ╚══════════════════════════════════════════╝

  Local:   http://localhost:{port}
  Tools:   {TOOLS_DIR}
  Builds:  {BUILDS_DIR}

  Open your browser to start building!
    """)
    webbrowser.open(f"http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    main()