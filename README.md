# PicoKey Manager for Android

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/Platform-Android%208.0%2B-green.svg)](https://www.android.com/)
[![Built with](https://img.shields.io/badge/Built%20with-Kivy%20%2F%20Buildozer-orange.svg)](https://kivy.org/)
[![Hardware testing](https://img.shields.io/badge/%E7%9C%9F%E6%9C%BA%E9%AA%8C%E8%AF%81-%E6%9C%AA%E8%BF%9B%E8%A1%8C-critical.svg)](#项目状态)
[![Authored by](https://img.shields.io/badge/%E4%BB%A3%E7%A0%81%E7%94%B1-AI%20%E7%BC%96%E5%86%99-8A2BE2.svg)](#ai-生成声明)

简体中文 | [English](README.en.md)

一个通过 USB OTG 连接 **PicoKey**（Pico HSM / Pico FIDO / Pico OpenPGP）的安卓应用。
它是桌面端 Python 库 [pypicokey](https://github.com/IsayIsee/pypicokey) 的安卓移植版，
最终打包成一个可直接安装的 APK。

用 OTG 转接线把设备插到手机上，就能读取设备信息、修改 PHY 配置（USB VID/PID、LED 引脚与亮度、
启用的 USB 接口）、让 LED 闪一下、重启设备，或重启进入 BOOTSEL 模式拖入新固件。

**下载**：已编译好的 APK 在本仓库的 [Releases](../../releases) 页面，直接取最新版本安装即可。

每次跑 **Build Android APK** 工作流，编译好的 APK 会**自动发布到 Releases**，
release notes 自动生成且为**中英双语**（含版本号、commit 号、安装步骤与注意事项）。
如果同一个 tag 的 release 已存在，工作流会替换里面的 APK 并更新说明，不会重复创建。

---

## AI 生成声明

**本仓库的代码由 AI 编写，并非 PicoKey 上游作者的作品。** 使用前请先审阅。由此有两点必须说明：

- 协议层有自动化自检覆盖，但**全部代码从未在真实 PicoKey 上运行过**（见[项目状态](#项目状态)）。
- 安卓移植部分（`usbhost.py`、`ccid.py`、`ctap.py`、`cbor_mini.py`、`detect.py`、`main.py`）
  是本项目新写的代码，其中的任何缺陷都属于本项目，与上游无关。

设备出现异常时，请优先怀疑这个 App。

---

## 为什么不能直接打包

`pypicokey` 通过两条通道与设备通信，而安卓上这两条都不存在：

| 桌面端依赖 | 安卓上的情况 | 本项目的做法 |
| --- | --- | --- |
| `pyscard`（PC/SC，CCID 智能卡通道） | 没有 pcscd，也没有 PC/SC 中间件 | 通过 pyjnius 调用安卓 USB 主机接口，自行发送 CCID 帧 |
| `pyusb` + `libusb`（rescue 通道） | 应用无法直接访问裸 USB | 同一套 CCID 帧，跑在 vendor `0xFF` 接口上 |

设备协议本身——CCID 组帧、APDU、PHY 的 TLV、CTAPHID——是纯 Python，原样沿用未作修改，
只替换了底层的"字节管道"。CCID 与 FIDO HID 两条通道均已实现，扫描时自动列出。

## 功能

桌面版 PicoKey App 存在的原因，是固件虽然跨平台，但 LED 接法、GPIO 映射、板卡身份这些
在编译时无从得知，必须到目标板上"开光"一次。这些几乎全部落在 PHY 配置块上，本项目已完整覆盖：

| 官方功能 | 对应实现 | 状态 |
| --- | --- | --- |
| 板卡身份识别 | USB VID/PID、USB 产品名 | ✅ |
| LED 行为 | LED GPIO、亮度、驱动（PICO / WS2812 / …）、常亮开关 | ✅ |
| GPIO 映射 | LED GPIO、确认按键（UP）GPIO | ✅ |
| USB 行为 | CCID / WCID / HID / KB 接口开关，WCID、DIMM、禁电源复位 | ✅ |
| 密码学能力 | 启用曲线位图（P-256/P-384/…/Ed25519/X25519，共 11 种） | ✅ |
| 安全启动 | 启动密钥槽（0-15）、永久锁定 | ✅ |
| 设备信息 | 平台、产品、固件版本、Flash 用量 | ✅ |
| 维护 | 重启、重启到 BOOTSEL、WINK 闪灯、FIDO getInfo | ✅ |
| 一键切换固件 | —— | ❌ 见下 |

- **设备扫描** — 枚举 USB 设备，列出所有可用通道：
  - `CCID` — 功能最全：设备信息、PHY、安全启动、重启
  - `rescue`（vendor `0xFF`）— 固件未启动或 PC/SC 不可用时的备用通道
  - `FIDO HID` — WINK、`authenticatorGetInfo`
- **中英双语界面** — 右上角可切换简体中文 / English，选择会被记住
- **内置协议自检** — 用假 USB 管道把协议栈跑一遍，无需硬件

**一键切换固件没有实现**，这一点说清楚：官方桌面版把各固件镜像打包在应用里，
本项目既没有这些镜像文件，也没有再分发的权利。要换固件，请用
**重启到 BOOTSEL** 进入 UF2 模式后在电脑上拖入。

## 使用方法

1. 用 **OTG 转接线**连接 PicoKey。
2. 打开 App → **扫描 USB 设备**，列表里会出现每个可用通道。
3. 点一个进行连接。手机会弹出 USB 授权对话框，**必须点允许**（只弹一次；
   若点了拒绝，需要到系统设置里重新开启）。
4. 设备页可用操作：
   - **重新读取设备信息** — 平台、产品、版本、Flash 用量
   - **读取 PHY 配置** — 把当前配置填入下方输入框
   - **写入 PHY 配置** — 应用改动，设备会重启
   - **WINK** — 让 LED 闪烁（仅 FIDO 通道）
   - **重启到 BOOTSEL** — 进入 UF2 模式

如果设备没被识别，先点**运行协议自检**——它不需要硬件。全绿就说明 App 本身没问题，
问题在 OTG 线、供电或转接头上。

## 目录结构

```
main.py                     Kivy 界面（扫描页 / 设备页 / 日志页），USB 操作都在子线程
picokeyapp/
  i18n.py                   中英文文案表与 t() 取值函数
  fonts.py                  中文字体注册（替换 Kivy 默认的 Roboto）
  usbhost.py                安卓 USB 主机接口封装：枚举、权限、claim、bulk IN/OUT
  ccid.py                   CCID 传输层（接上游的 ICCD 组帧）
  ctap.py                   CTAPHID 传输层（INIT / WINK / CBOR）
  cbor_mini.py              零依赖 CBOR 编解码（仅用于 authenticatorGetInfo）
  detect.py                 扫描设备，识别 ccid / rescue / fido 通道
  selftest.py               不需要硬件的协议自检
  pk/                       移植自上游的纯 Python 层（已去掉 pyscard / pyusb）
assets/fonts/               随包的中文字体（Noto Sans SC 子集，OFL 许可）
src/android/                构建时注入的 AndroidManifest 片段
buildozer.spec              Buildozer 打包配置
.github/workflows/          GitHub Actions 编译 APK
tools/fake_android_check.py 用假 jnius 驱动的集成检查
```

## 项目状态

已在开发环境验证（**未接硬件**）：

- `python3 -m picokeyapp.selftest` — CCID 组帧、APDU 收发、PHY TLV 解析、多包重组、
  CTAPHID 握手、CBOR 解析，全部与上游行为一致。
- `python3 tools/fake_android_check.py` — 用模拟的安卓 USB 主机 API 跑通整条链路
  （枚举 → 权限 → claim → 收发 → 三条通道各自建连）。
- Kivy 界面在无头环境下可启动、切页，报错路径正常。

**尚未验证**（需要真机）：

- USB 权限弹窗的实际行为、OTG 供电、不同厂商对 HID 接口的占用情况。
- 真实 PicoKey 的响应（上述测试用的是模拟设备）。
- 写入 PHY 后的实际效果。**第一次请只读取、不要写入**。

## 界面语言与中文字体

界面支持**简体中文**与 **English**，App 右上角的下拉框可切换，选择会写入
`ui_settings.json` 并记住。切换语言是重建一次界面，不会断开已连接的设备。

安卓上中文曾全部显示为方块（▯）：Kivy 默认字体 Roboto 不含中文字形，而 Kivy
也不会去用系统的中文字体。解决办法是随包带一份字体并在画任何控件之前注册
（`picokeyapp/fonts.py`）。用的是 **Noto Sans SC**（SIL OFL 1.1，允许嵌入），
并裁剪到 ASCII + GB2312 字符集，约 2 MB，而不是完整的 10 MB。

`buildozer.spec` 的 `source.include_exts` 必须包含 `ttf`，否则字体不会打进 APK，
中文又会变回方块。

## 已知限制

- 刻意没有打包 `cryptography` 与 `pycvc`：新版 `cryptography` 交叉编译需要 Rust 工具链，
  在 p4a 里容易失败。因此"安全通道 / DKEK"相关功能不可用，其余功能正常。
- 没有热插拔监听，拔线后回到扫描页重新连接即可。
- 需要 Android 8.0（API 26）以上、支持 USB host 的设备和一根 OTG 转接线。

## 故障排查

- **报 `Didn't find class "org.jnius.NativeInvocationHandler"`** — pyjnius 的已知坑。
  它只在**带有 Android 类加载器的线程**里才能解析 Java 类；Python 起的工作线程没有，
  JVM 于是报空 classpath（`DexPathList[[directory "."]]`）。该类是 pyjnius 为
  "Python 对象冒充 Java 接口"生成的代理，注册 BroadcastReceiver 时必须用到。
  本项目从两方面规避：USB 权限改用轮询 `UsbManager.hasPermission()`，完全不需要代理；
  同时在 `App.build()`（UI 线程）里预加载所有会用到的 Java 类，写进 pyjnius 缓存。
- **设备扫得到、一连就失败** — 多半是 USB 权限弹窗被拒。Android 只弹一次，
  拒了要去系统设置里重新允许，或卸载重装 App。

## 编译排错

- **报 `unrecognized arguments: --feature ...`** — 说明用了仍在设置 `android.features`
  的旧版 `buildozer.spec`。当前 python-for-android 已移除该参数，
  改为通过 `android.extra_manifest_xml` 注入声明。
- **卡在 "Installing/updating SDK platform tools"** — `sdkmanager` 在 CI 里等不到有人敲 `y`。
  用 `android.accept_sdk_license = True`，并在构建命令前加 `yes |` 兜底。
- **千万不要提前创建 `~/.buildozer/android/platform/android-sdk/`** —
  buildozer 判断 SDK 是否已安装时只看该路径是否存在，目录同样算"存在"。
  提前创建会导致它跳过下载，随后报 "sdkmanager is not installed"。
- **Gradle 报 JDK 版本不对** — API 35 需要 JDK 17，工作流已用 `actions/setup-java` 强制指定。
- **写入 PHY 配置**会改动设备设置并重启。先读，确认数值无误再写。

## 许可证

上游 `pypicokey` 为 AGPL-3.0-or-later，`picokeyapp/pk/` 下的文件沿用该许可
（见 `LICENSE`）；安卓移植与界面部分同样以 AGPL-3.0-or-later 发布。

随包的字体 `assets/fonts/NotoSansSC-Regular-subset.ttf` 来自
[Noto Sans SC](https://fonts.google.com/noto/specs/NotoSansSC)，
以 SIL Open Font License 1.1 授权（允许嵌入与再分发），不受本项目 AGPL 约束。
