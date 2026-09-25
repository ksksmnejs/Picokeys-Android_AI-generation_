"""
Bilingual UI strings.

Why this exists
---------------
The app was originally written with hard-coded Chinese text, which rendered as
tofu boxes on Android: Kivy's bundled font (Roboto) has no CJK glyphs. The fix
is two-fold - ship a CJK font (see picokeyapp/fonts.py) and put every visible
string behind `t()` so the whole UI can switch between 简体中文 and English.

Usage
-----
    from .i18n import t, set_lang, get_lang
    t('btn_scan')                  # -> '扫描 USB 设备' / 'Scan USB devices'
    t('scan_found', n=3)           # -> '找到 3 个通道…'

Keys are stable English identifiers; adding a language means adding a dict.
"""

from __future__ import annotations

LANGS = ("zh", "en")
DEFAULT_LANG = "zh"

# Language names are always shown in their own language, like every decent
# language picker does.
LANG_NAMES = {"zh": "简体中文", "en": "English"}

_current = DEFAULT_LANG

STRINGS = {
    # ------------------------------------------------------------ generic
    "app_title": {"zh": "PicoKey Manager", "en": "PicoKey Manager"},
    "language": {"zh": "语言", "en": "Language"},
    "btn_scan": {"zh": "扫描 USB 设备", "en": "Scan USB devices"},
    "btn_selftest": {"zh": "运行协议自检（无需硬件）", "en": "Run protocol self-test (no hardware)"},
    "btn_logs": {"zh": "查看日志", "en": "View log"},
    "btn_back": {"zh": "返回", "en": "Back"},
    "btn_clear": {"zh": "清空", "en": "Clear"},
    "btn_disconnect": {"zh": "断开连接", "en": "Disconnect"},
    "btn_back_scan": {"zh": "返回扫描页", "en": "Back to scan"},

    # ------------------------------------------------------------ scan page
    "scan_intro": {
        "zh": "把 PicoKey 用 OTG 转接线插到手机上，然后点“扫描 USB 设备”。",
        "en": "Plug the PicoKey into the phone with an OTG adapter, then press “Scan USB devices”.",
    },
    "scanning": {"zh": "扫描中…", "en": "Scanning…"},
    "scan_none_hint": {
        "zh": "没找到可用设备。检查 OTG 线和供电，或点“查看日志”。",
        "en": "No device found. Check the OTG cable and power, or open the log.",
    },
    "scan_none_item": {"zh": "（无设备）", "en": "(no device)"},
    "scan_found": {"zh": "找到 {n} 个通道，点一个连接：", "en": "{n} channel(s) found, tap one to connect:"},
    "connecting": {"zh": "连接中（手机上要允许 USB 权限）…", "en": "Connecting (allow USB access on the phone)…"},
    "connected": {"zh": "已连接", "en": "Connected"},

    # ---------------------------------------------------------- device page
    "not_connected": {"zh": "未连接", "en": "Not connected"},
    "lbl_platform": {"zh": "平台", "en": "Platform"},
    "lbl_product": {"zh": "产品", "en": "Product"},
    "lbl_version": {"zh": "版本", "en": "Version"},
    "lbl_channel": {"zh": "通道", "en": "Channel"},
    "lbl_flash": {"zh": "Flash", "en": "Flash"},
    "lbl_files": {"zh": "文件数", "en": "Files"},
    "lbl_firmware": {"zh": "固件", "en": "Firmware"},
    "lbl_protocol": {"zh": "协议版本", "en": "Protocol"},
    "lbl_device_ver": {"zh": "设备版本", "en": "Device version"},
    "lbl_caps": {"zh": "能力", "en": "Capabilities"},
    "lbl_cid": {"zh": "CID", "en": "CID"},
    "flash_line": {
        "zh": "Flash：已用 {used:.1f}KB / 共 {total:.1f}KB，剩余 {free:.1f}KB",
        "en": "Flash: {used:.1f}KB used / {total:.1f}KB total, {free:.1f}KB free",
    },
    "files_line": {"zh": "文件数：{n}，固件：{size:.1f}KB", "en": "Files: {n}, firmware: {size:.1f}KB"},

    "btn_refresh": {"zh": "重新读取设备信息", "en": "Re-read device info"},
    "btn_read_phy": {"zh": "读取 PHY 配置", "en": "Read PHY config"},
    "field_vid": {"zh": "VID (hex)", "en": "VID (hex)"},
    "field_pid": {"zh": "PID (hex)", "en": "PID (hex)"},
    "field_led_gpio": {"zh": "LED GPIO", "en": "LED GPIO"},
    "field_led_btness": {"zh": "LED 亮度 (0-255)", "en": "LED brightness (0-255)"},
    "field_led_driver": {"zh": "LED 驱动", "en": "LED driver"},
    "btn_write_phy": {"zh": "写入 PHY 配置（会重启设备）", "en": "Write PHY config (reboots device)"},
    "btn_wink": {"zh": "WINK：让 LED 闪一下（FIDO）", "en": "WINK: blink the LED (FIDO)"},
    "btn_reboot": {"zh": "重启设备", "en": "Reboot device"},
    "btn_reboot_bootsel": {"zh": "重启到 BOOTSEL（拖固件用）", "en": "Reboot to BOOTSEL (for firmware)"},

    # ------------------------------------------------------------ log page
    "log_title": {"zh": "日志 / APDU", "en": "Log / APDU"},

    # ------------------------------------------------------------- channels
    "ch_ccid_title": {"zh": "CCID 智能卡通道", "en": "CCID smartcard channel"},
    "ch_ccid_detail": {
        "zh": "走 CCID 帧的 APDU，功能最全（设备信息 / PHY / 重启）",
        "en": "APDU over CCID frames, full feature set (info / PHY / reboot)",
    },
    "ch_rescue_title": {"zh": "救援通道 (vendor 0xFF)", "en": "Rescue channel (vendor 0xFF)"},
    "ch_rescue_detail": {
        "zh": "固件没起来或 PC/SC 不可用时的备用通道，同样是 CCID 帧",
        "en": "Fallback when firmware is down or PC/SC is unusable, same CCID frames",
    },
    "ch_fido_title": {"zh": "FIDO HID 通道", "en": "FIDO HID channel"},
    "ch_fido_detail": {
        "zh": "CTAPHID：WINK 闪灯、读 authenticatorGetInfo",
        "en": "CTAPHID: WINK blinking, authenticatorGetInfo",
    },

    # ------------------------------------------------------- status messages
    "msg_processing": {"zh": "处理中…", "en": "Working…"},
    "msg_refreshed": {"zh": "已刷新", "en": "Refreshed"},
    "msg_reading": {"zh": "读取中…", "en": "Reading…"},
    "msg_writing_phy": {"zh": "写入 PHY…", "en": "Writing PHY…"},
    "msg_reading_phy": {"zh": "读取 PHY…", "en": "Reading PHY…"},
    "msg_winking": {"zh": "发送 WINK…", "en": "Sending WINK…"},
    "msg_rebooting": {"zh": "重启中…", "en": "Rebooting…"},
    "msg_phy_read": {
        "zh": "PHY 已读取：VID={vid} PID={pid} LED_GPIO={gpio} 亮度={btness}",
        "en": "PHY read: VID={vid} PID={pid} LED_GPIO={gpio} brightness={btness}",
    },
    "msg_phy_written": {"zh": "PHY 已写入，设备正在重启", "en": "PHY written, device is rebooting"},
    "msg_phy_written_log": {
        "zh": "PHY 写入完成，重新插拔或重新扫描即可连回。",
        "en": "PHY write done. Re-plug or re-scan to reconnect.",
    },
    "msg_wink_sent": {"zh": "已发送 WINK，看设备 LED", "en": "WINK sent - watch the device LED"},
    "msg_reboot_sent": {"zh": "已发送重启命令", "en": "Reboot command sent"},
    "msg_disconnected": {"zh": "已断开", "en": "Disconnected"},
    "msg_selftest_running": {"zh": "自检中…", "en": "Self-testing…"},
    "msg_selftest_done": {"zh": "自检完成，详见日志", "en": "Self-test done, see the log"},
    "msg_failed": {"zh": "失败：{err}", "en": "Failed: {err}"},
    "msg_closed_error": {"zh": "关闭时出错：{err}", "en": "Error while closing: {err}"},
    "msg_connected_log": {"zh": "已连接：{label}", "en": "Connected: {label}"},
    "msg_getinfo_failed": {"zh": "getInfo 失败：{err}", "en": "getInfo failed: {err}"},
    "msg_reconnect_needed": {"zh": "请重新读取或重新连接", "en": "Re-read or reconnect"},

    # ---------------------------------------------------------------- errors
    "err_no_apdu": {"zh": "当前通道不支持 APDU（这是 FIDO HID 通道）", "en": "This channel has no APDU support (it is the FIDO HID channel)"},
    "err_phy_read": {"zh": "读取 PHY 失败", "en": "Reading PHY failed"},
    "err_not_android": {"zh": "USB Host 只在安卓真机上可用（当前：{plat}）", "en": "USB host only works on a real Android device (current: {plat})"},
    "err_permission_denied": {
        "zh": "USB 权限被拒绝（弹窗里要点“允许”，并且只弹一次）",
        "en": "USB permission denied (tap Allow in the dialog - it is asked only once)",
    },
    "err_no_permission": {"zh": "UsbManager 仍然没有权限", "en": "UsbManager still has no permission"},
    "err_not_fido": {"zh": "这个 HID 接口不像 FIDO 设备（报告描述符里没有 usage page 0xF1D0）", "en": "This HID interface does not look like FIDO (no 0xF1D0 usage page in the report descriptor)"},
    "err_claim_failed": {"zh": "接口占用失败（多半是内核 HID 驱动占着）", "en": "Could not claim the interface (a kernel HID driver probably holds it)"},
    "err_open_device": {"zh": "无法打开设备（没有权限或设备忙）", "en": "Cannot open the device (no permission or device busy)"},
    "err_no_endpoints": {"zh": "这个接口没有可用的 IN/OUT 端点", "en": "This interface has no usable IN/OUT endpoints"},

    # ------------------------------------------------------------- self-test
    "selftest_title": {"zh": "协议自检", "en": "Protocol self-test"},
    "selftest_cbor": {"zh": "CBOR 编解码", "en": "CBOR codec"},
    "selftest_ccid": {"zh": "CCID 组帧 / APDU", "en": "CCID framing / APDU"},
    "selftest_ctap": {"zh": "CTAPHID / FIDO", "en": "CTAPHID / FIDO"},
    "selftest_passed": {
        "zh": "全部通过：协议层行为与上游一致。",
        "en": "All checks passed: protocol behaviour matches upstream.",
    },
}


def get_lang() -> str:
    return _current


def set_lang(code: str) -> str:
    global _current
    if code in LANGS:
        _current = code
    return _current


def t(key: str, **kwargs) -> str:
    """Translate `key` into the current language, then format it."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_current) or entry.get(DEFAULT_LANG) or key
    try:
        return text.format(**kwargs) if kwargs else text
    except Exception:
        return text


def lang_name(code: str) -> str:
    return LANG_NAMES.get(code, code)
