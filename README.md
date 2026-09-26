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
支持的芯片包括 **RP2040、RP2350、ESP32-S2、ESP32-S3**（见[支持的开发板](#支持的开发板)）。

用 OTG 转接线把设备插到手机上，就能读取设备信息、修改 PHY 配置（USB VID/PID、LED 引脚与亮度、
启用的 USB 接口）、让 LED 闪一下、重启设备，或进入刷机模式写入新固件。

**下载**：已编译好的 APK 在本仓库的 [Releases](../../releases) 页面，取最新版本安装即可；
**早期版本也保留在同一个页面**，随时可以回退（见[版本历史](#版本历史)）。

每次跑 **Build Android APK** 工作流，编译好的 APK 会**自动发布到 Releases**，
release notes 自动生成且为**中英双语**（含版本号、commit 号、安装步骤与注意事项）。
如果同一个 tag 的 release 已存在，工作流会替换里面的 APK 并更新说明，不会重复创建。

---

## AI 生成声明

**本仓库的代码由 AI 编写，并非 PicoKey 上游作者的作品。** 使用前请先审阅。由此有两点必须说明：

- 协议层有自动化自检覆盖，但**全部代码从未在真实 PicoKey 上运行过**（见[项目状态](#项目状态)）。
- 安卓移植部分（`usbhost.py`、`ccid.py`、`ctap.py`、`cbor_mini.py`、`detect.py`、
  `flasher.py`、`main.py`）
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

## 版本历史

每次发布都会**新建一个 release，不再覆盖旧的**。所以升级后如果新版本有问题，
可以回到 Releases 页面下载之前的任何一个版本。

| 版本 | 主要变化 |
| --- | --- |
| **v0.2.0** | 新增「固件刷写」页（UF2 识别 + ESP32 ROM 串口协议）；修复状态栏遮挡顶部内容；修复长英文按钮文字被截断；文档补齐 RP2040/RP2350/ESP32-S2/S3 差异；release notes 改为中英双语 |
| **v0.1.0** | 首个版本。USB OTG 连接、三通道扫描（CCID / rescue / FIDO HID）、读取设备信息、PHY 配置读写、安全启动、重启与进入刷机模式、WINK、协议自检、中英双语界面 |

完整列表见 [Releases](../../releases) 页面。

### 发布新版本

版本号写在 `buildozer.spec` 的 `version` 字段，工作流用它生成 release tag：

```ini
version = 0.2.0    # 改成 0.3.0 就是下一个版本
```

**发布前请先提升这个数字。** 工作流在检测到同名 tag 已存在时，默认会**直接失败并提示**，
而不是静默覆盖——这正是为了保住历史版本。如果确实想原地替换当前版本，
在 Run workflow 时勾选 **overwrite** 即可。

### 版本号的习惯

- 修 bug、小改动 → 最后一位（`0.2.0` → `0.2.1`）
- 加功能 → 中间一位（`0.2.0` → `0.3.0`）
- 大改或不兼容变更 → 第一位（`0.2.0` → `1.0.0`）

## 支持的开发板

PicoKeys 固件跑在四种芯片上。协议层完全一样，差别全在**刷机方式、进入刷机模式的手势、
以及安全特性**上——这也是这个 App 需要按板子区分对待的唯一原因。

| 芯片 | 典型板子 | 刷机方式 | 进刷机模式 | Secure Boot / Lock |
| --- | --- | --- | --- | --- |
| **RP2040** | Raspberry Pi Pico / Pico W | UF2（BOOTSEL 变 U 盘） | 按住 BOOTSEL 插入 | ❌ 无硬件保护 |
| **RP2350** | Pico 2、Waveshare RP2350-One/Zero/Tiny | UF2（BOOTSEL 变 U 盘） | 按住 BOOTSEL 插入 | ✅ 完整支持 |
| **ESP32-S2** | ESP32-S2 开发板 | esptool / DFU | 按住 BOOT → 按 RESET → 松 RESET → 松 BOOT | ⚠️ 见下 |
| **ESP32-S3** | ESP32-S3 SuperMini、DevKitC | esptool / DFU | 同上 | ⚠️ 见下 |

### RP2040 与 RP2350 的区别（不只是主频）

两者都用 UF2，但**安全性完全不同**：

- RP2350 有一个 OTP（一次性可编程）区，可存放加密所有密钥的主密钥（MKEK），
  配合 Secure Boot / Secure Lock 能抵抗 flash 被读出。
- **RP2040 没有这套硬件**。它的 flash 内容可直接读取，板子丢了里面的私钥就暴露了。

所以如果安全性是目的，请用 RP2350 或 ESP32-S3，别用 RP2040。

### ESP32-S2 / S3 的两个特殊之处

**1. 两个 USB 控制器共用一个 PHY**

ESP32-S3 内部有 USB Serial/JTAG（固定功能，用于烧录和调试）和 USB-OTG（可编程，
TinyUSB）两个控制器，但它们**共用同一个内部 USB PHY**，同一时刻只能有一个占用那个
原生 USB 口。固件跑起来时用的是其中一个；进下载模式时是另一个。

**2. 下载模式下设备名会变**

进下载模式后，设备会自报为 **"USB JTAG/serial debug unit"**（VID/PID 也和运行时不同）。
这不是 PicoKey 的 CCID 接口，**对它发 CCID 指令不会有任何回应**。

如果你的 App 日志里看到这个名字，说明板子正卡在下载模式——**拔掉、什么都不按、重新插**，
让固件正常启动。这也是本项目在检测到这个名字时会弹窗提醒的原因。

### 关于 Secure Boot 在 ESP32 上

官方 README 声称 ESP32-S3 支持 Secure Boot 与 Secure Lock，但社区分叉（LibreKeys）的
支持矩阵里这两项对 ESP32-S2/S3 标注的是 `No (// TODO)`，只有 RP2350 是完整支持。
两边说法不一致，**本项目无法替你确认**。

实践建议：先点「读取安全启动状态」。如果读不出来或读到的值异常，就说明该功能在这块
板子上没实现，**不要硬写**——OTP 熔丝烧错了是物理级不可逆的。

### 出厂 VID/PID

2026 年 1 月起，固件出厂就用树莓派正式分配的 USB ID，不再需要为了"被系统识别"而开光：

| 固件 | VID:PID |
| --- | --- |
| Pico HSM | `2E8A:10FD` |
| Pico FIDO | `2E8A:10FE` |
| Pico OpenPGP | `2E8A:10FF` |

更早的固件用的是占位 ID `FEFF:FCFD`，那种才必须改。**如果你的目的是"当个能用的 FIDO2
密钥"且 VID/PID 已经是上表中的值，那就什么都不用配**——改 VID/PID 主要是为了伪装成
YubiKey（让某些网站或 Yubico Authenticator 认）。

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
| 安全启动 | 启动密钥槽（0-15）、永久锁定 | ⚠️ 仅 RP2350 确认可用，ESP32 存疑 |
| 设备信息 | 平台、产品、固件版本、Flash 用量 | ✅ |
| 维护 | 重启、进入刷机模式、WINK 闪灯、FIDO getInfo | ✅ |
| 一键切换固件 | —— | ❌ 见下 |

- **设备扫描** — 枚举 USB 设备，列出所有可用通道：
  - `CCID` — 功能最全：设备信息、PHY、安全启动、重启
  - `rescue`（vendor `0xFF`）— 固件未启动或 PC/SC 不可用时的备用通道
  - `FIDO HID` — WINK、`authenticatorGetInfo`
- **中英双语界面** — 右上角可切换简体中文 / English，选择会被记住
- **内置协议自检** — 用假 USB 管道把协议栈跑一遍，无需硬件

**一键切换固件没有实现**，这一点说清楚：官方桌面版把各固件镜像打包在应用里，
本项目既没有这些镜像文件，也没有再分发的权利。要换固件，请用**进入刷机模式**
（RP2040/RP2350 是 BOOTSEL，ESP32 是 BOOT+RESET）后自行写入。
具体实现见[固件刷写](#固件刷写)。

## 使用方法

1. 用 **OTG 转接线**连接 PicoKey。**不要按任何按键**——按住 BOOT/BOOTSEL 插入会让
   板子进刷机模式，此时它不是 PicoKey，App 连不上（ESP32 会显示为
   "USB JTAG/serial debug unit"）。
2. 打开 App → **扫描 USB 设备**，列表里会出现每个可用通道。
3. 点一个进行连接。手机会弹出 USB 授权对话框，**必须点允许**（只弹一次；
   若点了拒绝，需要到系统设置里重新开启）。
4. 设备页可用操作：
   - **重新读取设备信息** — 平台、产品、版本、Flash 用量
   - **读取 PHY 配置** — 把当前配置填入下方输入框
   - **写入 PHY 配置** — 应用改动，设备会重启
   - **WINK** — 让 LED 闪烁（仅 FIDO 通道）
   - **进入刷机模式** — RP2040/RP2350 进 BOOTSEL，ESP32 进下载模式

如果设备没被识别，先点**运行协议自检**——它不需要硬件。全绿就说明 App 本身没问题，
问题在 OTG 线、供电或转接头上。

### 首次使用的建议顺序

1. **先只读取，不写入** — 确认能读到设备信息，说明链路是通的
2. 需要改 VID/PID 时，留空字段会自动继承设备当前值，不会冲掉 LED GPIO 这类板子特定配置
3. **启用曲线至少勾 P-256**（ES256，WebAuthn 最通用的默认算法）+ 可选 Ed25519；
   **不要勾 secp256k1** — 官方文档明确警告部分旧安卓设备不支持它，启用后设备可能无法识别
4. **安全启动留到最后**，且需满足：已注册通行密钥并日常验证过、有备份、
   确认刷的是官方原版固件、接受不可逆后果

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
  flasher.py                固件刷写：UF2 识别 + ESP32 ROM 串口协议（SLIP/FLASH_*）
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
`ui_settings.json` 并记住。切换语言是重建三个界面的内容，不会断开已连接的设备。

> **实现说明**：界面各屏用**匿名根 widget**构建，而不是 `<Screen>:` 类规则。
> 类规则会被 Builder 注册到类上，重复加载不是"替换"而是"追加"——早期版本每次切语言
> 都往屏幕上叠一整套新语言的控件（3 个按钮 → 6 → 9…），表现为"一半中文一半英文、
> 按钮点不动"。匿名根只产生实例、不产生类规则，因此不会累积。

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
- **RP2040 没有 OTP 硬件保护**，其 flash 内容可被直接读出；需要防物理提取请用
  RP2350 或 ESP32-S3（且需确认 Secure Boot 在该板子上确实可用）。
- **ESP32-S2/S3 的 Secure Boot / Secure Lock 支持情况存疑**，官方与社区分叉说法不一致。
  本项目只提供读取与写入接口，不做判断——请先读，读不通就别写。
- 三种固件（HSM / FIDO / OpenPGP）**不能共存**，切换需先刷 Pico Nuke 清空。
  建议按用途各用一块板子，而不是来回切换。

## 故障排查

- **报 `Didn't find class "org.jnius.NativeInvocationHandler"`** — pyjnius 的已知坑。
  它只在**带有 Android 类加载器的线程**里才能解析 Java 类；Python 起的工作线程没有，
  JVM 于是报空 classpath（`DexPathList[[directory "."]]`）。该类是 pyjnius 为
  "Python 对象冒充 Java 接口"生成的代理，注册 BroadcastReceiver 时必须用到。
  本项目从两方面规避：USB 权限改用轮询 `UsbManager.hasPermission()`，完全不需要代理；
  同时在 `App.build()`（UI 线程）里预加载所有会用到的 Java 类，写进 pyjnius 缓存。
- **设备扫得到、一连就失败** — 多半是 USB 权限弹窗被拒。Android 只弹一次，
  拒了要去系统设置里重新允许，或卸载重装 App。
- **日志里出现 "USB JTAG/serial debug unit"（ESP32）** — 板子在下载模式，不是 PicoKey。
  拔掉、什么都不按、重新插。
- **ESP32 上安全启动读不出来** — 大概率该功能在这块板子上没实现（官方说法与社区分叉
  不一致）。不要硬写，OTP 熔丝不可逆。
- **中文显示成方块（▯）** — `assets/fonts/` 没传，或 `buildozer.spec` 的
  `source.include_exts` 不含 `ttf`，字体没被打进 APK。

## 固件刷写

App 里有一个「固件刷写」页（扫描页底部按钮进入）。它处理两种**机制完全不同**的路径：

| 板子 | 底层机制 | 本 App 的做法 |
|---|---|---|
| RP2040 / RP2350 | BOOTSEL 后 Boot ROM 把 flash 暴露成 USB 大容量存储设备（U 盘），拷入 `.uf2` 即完成 | 把 UF2 交给系统文件管理器，由你存到 `RPI-RP2`（RP2040）或 `RP2350` 盘里 |
| ESP32-S2 / S3 | USB Serial/JTAG 上的 esptool ROM 串口协议，**没有 UF2 bootloader** | 直接实现该协议（SLIP 组帧 + FLASH_BEGIN/DATA/END），不需要外部工具 |

固件可以来自本地文件，也可以填一个 https 地址下载。选好后 App 会识别格式
（UF2 / ESP 镜像 / ZIP / gzip / 误下载成网页）并显示大小和适用芯片。

### 各板子进刷机模式的手势

**RP2040 / RP2350**：按住 **BOOTSEL** → 插入 USB → 松开。手机上会多出一个 U 盘，
把 UF2 存进去，盘符自动消失即刷写完成。连驱动都不用装。

**ESP32-S2 / S3**：按住 **BOOT** → 按一下 **RESET** → 松开 RESET → 松开 BOOT。
顺序错了、或只按了 BOOT 没按 RESET，芯片就还在跑旧程序。进下载模式后设备名会变成
"USB JTAG/serial debug unit"。

⚠️ **两条刷写路径都没有在真机上验证过。**

- ESP32 出错**通常可以重来**（ROM 下载模式还在，能救回），这是它的优势
- RP2040/RP2350 的 UF2 路径只是委托给系统文件管理器，本身是可靠的
- 第一次建议**只做识别、不刷写**，对着日志确认每一步再动

另外 ESP32-S3 想让 USB-OTG 彻底接管那个口，需要烧 `USB_PHY_SEL` eFuse——
**永久不可逆**。本项目不会引导你这么做。

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
