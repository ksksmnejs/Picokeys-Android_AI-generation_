# PicoKey Manager for Android

把 [pypicokey](https://github.com/IsayIsee/pypicokey)（Pico HSM / Pico FIDO / Pico OpenPGP
的管理库）搬到安卓上，做成一个能装在手机里的 APK：OTG 转接线一插，就能在手机上读设备信息、
改 PHY 配置（VID/PID、LED）、让 LED 闪一下、重启，或重启进 BOOTSEL 拖固件。

## 为什么不能"直接打包"

pypicokey 在电脑上靠两条路跟设备通信，安卓上两条都不存在：

| 桌面端依赖 | 安卓的情况 | 这里的做法 |
| --- | --- | --- |
| `pyscard`（PC/SC，走 CCID 智能卡通道） | 安卓没有 pcscd，也没有 PC/SC 中间件 | 用 pyjnius 直接调安卓 USB 主机接口，自己发 CCID 帧 |
| `pyusb` + `libusb`（rescue 通道） | 普通应用拿不到裸 USB | 同上，同一套 CCID 帧跑到 vendor 0xFF 接口上 |

设备协议本身（CCID 组帧、APDU、PHY 的 TLV、CTAPHID）是纯 Python，一行没改，只是把底下那层
"字节管道"换掉了。按你的要求，CCID 和 FIDO HID 两条通道都实现了，扫描时自动列出来。

## 目录结构

```
main.py                     Kivy 界面（扫描页 / 设备页 / 日志页），所有 USB 操作都在子线程
picokeyapp/
  usbhost.py                安卓 USB 主机接口封装：枚举、权限、claim、bulk IN/OUT
  ccid.py                   CCID 传输层（接上游的 ICCD 组帧）
  ctap.py                   CTAPHID 传输层（INIT / WINK / CBOR）
  cbor_mini.py              零依赖 CBOR 编解码（只为读 authenticatorGetInfo）
  detect.py                 扫描设备，识别 ccid / rescue / fido 三种通道
  selftest.py               不需要硬件的协议自检
  pk/                       移植自上游的纯 Python 层（已去掉 pyscard / pyusb）
buildozer.spec              Buildozer 打包配置
.github/workflows/build-apk.yml   GitHub Actions 云端编译 APK
tools/fake_android_check.py  用假 jnius 跑通整条链路的集成检查
```

## 怎么得到 APK

你只有手机、没有电脑，所以本地 `buildozer android debug` 这条路走不通（需要 SDK/NDK，
Termux 里也装不完整）。用 GitHub Actions 免费编译：

1. 把这个目录整体上传到一个 GitHub 仓库（保留 `.github/` 目录）。
2. 打开仓库的 **Actions** 页，选 **Build Android APK**，点 **Run workflow**。
3. 跑完（通常 15–40 分钟）在 Artifacts 里下载 `picokey-manager-debug`，解压得到 APK。
4. 手机安装。第一次打开如果没有自动弹"USB 权限"，去系统设置里看有没有被静默拒绝。

有 Linux 环境的话，等价的本地命令是：
```bash
pip install "Cython==3.0.12" buildozer
buildozer -v android debug     # 产物在 bin/
```

## 手机上怎么用

1. PicoKey 用 **OTG 转接线**插到手机上（注意供电，Pico 系列电流不大但 RP2350 板子带灯会高一些）。
2. 打开 App → 点 **扫描 USB 设备**，列表里会出现每个可用通道，例如：
   - `CCID 智能卡通道` — 功能最全，设备信息 / PHY / 安全启动 / 重启
   - `救援通道 (vendor 0xFF)` — 固件没起来或 PC/SC 不可用时的备用通道
   - `FIDO HID 通道` — WINK 闪灯、读 authenticatorGetInfo
3. 点一个连接。手机会弹 USB 授权，**必须点允许**（只弹一次，拒了要去设置里改）。
4. 连接后：
   - **重新读取设备信息** — 平台 / 产品 / 版本 / Flash 用量
   - **读取 PHY 配置** — 把当前的 VID/PID、LED GPIO、亮度、USB 接口开关填进下面输入框
   - **写入 PHY 配置** — 改完点这个，设备会重启生效
   - **WINK** — 让 LED 闪一下，最快的"还活着吗"测试（仅 FIDO 通道）
   - **重启到 BOOTSEL** — 进 UF2 模式，方便在电脑上拖固件

不确定设备有没有被识别，先点 **运行协议自检**：它不需要硬件，用假 USB 管道把协议层跑一遍，
全绿说明 App 本身没问题，问题在硬件/供电/OTG 线上。

## 编译排错

- **卡在 `Installing/updating SDK platform tools` 然后失败**：sdkmanager 在没有终端的 CI 里
  没法等你敲 `y`。修法是 `buildozer.spec` 里的 `android.accept_sdk_license = True`
  （buildozer 用 pexpect 自动回 `y`），外加构建命令前面的 `yes |` 兜底。
- **千万不要提前创建 `~/.buildozer/android/platform/android-sdk` 目录**：buildozer 判断
  "SDK 装没装" 用的是 `Path(sdk_dir).exists()`，对目录一样返回 True。所以哪怕只是往里面
  放一个许可文件，buildozer 也会认为 SDK 已就绪、跳过下载，接着报
  `sdkmanager path does not exist, sdkmanager is not installed`。踩过一次，别再踩。
- **Gradle 报 JDK 版本不对 / `Unsupported class file major version`**：说明 buildozer 抓到了
  系统自带的 JDK 11。API 35 对应 AGP/Gradle 需要 JDK 17，工作流里已用 `setup-java` 强制。
- **失败后想看细节**：工作流带一步 "Dump buildozer logs on failure"，会把 `.buildozer`
  里最后几个日志的末尾 120 行打出来，直接贴出来排查。

## 已经验证过的 / 没验证过的

已在开发环境跑通（无需硬件）：

- 协议自检 `python3 -m picokeyapp.selftest`：CCID 组帧、APDU、PHY TLV 解析、多包重组、
  CTAPHID 握手、CBOR 解析全部与上游行为一致。
- 集成检查 `python3 tools/fake_android_check.py`：用一个模拟安卓 USB 主机 API 的假 `jnius`
  跑通"枚举 → 权限 → claim → 收发 → 三条通道各自建连"。
- Kivy 界面在无头环境下真实启动、切页、报错路径与内置自检均正常。

没验证过的（需要真机）：

- 真机上的 USB 权限弹窗行为、OTG 供电、不同厂商对 HID 接口的占用情况。
- 真 PicoKey 的 CCID/FIDO 响应（上面的自检用的是模拟设备）。
- 写入 PHY 后的实际重启行为 —— 这个操作会改设备配置，**第一次建议先只读不写**。

## 已知取舍

- 没有打包 `cryptography` / `pycvc`：新版 cryptography 需要 Rust 工具链交叉编译，在 p4a 里
  很容易翻车。缺这两个只影响"安全通道 / DKEK"相关功能，其他都正常；要用就自己在
  `buildozer.spec` 的 `requirements` 里加上并做好编译失败的准备。
- 没有 PC/SC 层的热插拔监听，拔线后回扫描页重连即可。

## 许可证

上游 pypicokey 是 AGPL-3.0-or-later，本项目的 `picokeyapp/pk/` 下文件沿用同一许可
（见 `LICENSE`）；安卓适配与界面部分同样按 AGPL-3.0-or-later 发布。
