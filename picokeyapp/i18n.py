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


# ---------------------------------------------------------------------------
# Commissioning (the extra PHY options and curves) and secure boot.
# Kept in a second block so the general UI strings above stay readable.
# ---------------------------------------------------------------------------
STRINGS.update({
    # ------------------------------------------------------------ sections
    "sec_phy": {"zh": "—— PHY 配置 ——", "en": "—— PHY configuration ——"},
    "sec_opts": {"zh": "—— 选项 ——", "en": "—— Options ——"},
    "sec_curves": {"zh": "—— 启用曲线（HSM）——", "en": "—— Enabled curves (HSM) ——"},
    "sec_security": {"zh": "—— 安全启动 ——", "en": "—— Secure boot ——"},
    "sec_firmware": {"zh": "—— 固件与重启 ——", "en": "—— Firmware & reboot ——"},

    # ------------------------------------------------------- extra PHY fields
    "field_usb_product": {"zh": "USB 产品名", "en": "USB product"},
    "field_up_btn": {"zh": "确认按键 GPIO", "en": "Confirm button GPIO"},

    # ----------------------------------------------------------------- OPTS
    "opt_wcid": {"zh": "WCID", "en": "WCID"},
    "opt_dimm": {"zh": "呼吸灯", "en": "DIMM"},
    "opt_no_reset": {"zh": "禁电源复位", "en": "No power reset"},
    "opt_led_steady": {"zh": "LED 常亮", "en": "LED steady"},

    # ---------------------------------------------------------------- curves
    "cv_secp256r1": {"zh": "P-256", "en": "P-256"},
    "cv_secp384r1": {"zh": "P-384", "en": "P-384"},
    "cv_secp521r1": {"zh": "P-521", "en": "P-521"},
    "cv_secp256k1": {"zh": "secp256k1", "en": "secp256k1"},
    "cv_bp256r1": {"zh": "BP-256", "en": "BP-256"},
    "cv_bp384r1": {"zh": "BP-384", "en": "BP-384"},
    "cv_bp512r1": {"zh": "BP-512", "en": "BP-512"},
    "cv_ed25519": {"zh": "Ed25519", "en": "Ed25519"},
    "cv_ed448": {"zh": "Ed448", "en": "Ed448"},
    "cv_curve25519": {"zh": "X25519", "en": "X25519"},
    "cv_curve448": {"zh": "X448", "en": "X448"},
    "curves_all": {"zh": "全选", "en": "All"},
    "curves_none": {"zh": "全不选", "en": "None"},
    "curves_value": {"zh": "曲线位图：0x{v:08X}", "en": "Curve bitmap: 0x{v:08X}"},

    # ----------------------------------------------------------- secure boot
    "btn_read_secure": {"zh": "读取安全启动状态", "en": "Read secure boot status"},
    "btn_secure_boot": {"zh": "设置安全启动密钥", "en": "Set secure boot key"},
    "field_bootkey": {"zh": "启动密钥槽 (0-15)", "en": "Boot key slot (0-15)"},
    "chk_lock": {"zh": "永久锁定（不可撤销）", "en": "Lock permanently (irreversible)"},
    "lbl_secure_enabled": {"zh": "安全启动", "en": "Secure boot"},
    "lbl_secure_locked": {"zh": "已锁定", "en": "Locked"},
    "lbl_bootkey": {"zh": "启动密钥槽", "en": "Boot key slot"},
    "lbl_yes": {"zh": "是", "en": "Yes"},
    "lbl_no": {"zh": "否", "en": "No"},
    "hint_bootkey": {
        "zh": "锁定后该密钥不可再更改，请确认槽位正确。",
        "en": "Once locked the key cannot be changed. Check the slot first.",
    },

    "msg_secure_reading": {"zh": "读取安全启动状态…", "en": "Reading secure boot status…"},
    "msg_secure_writing": {"zh": "写入安全启动配置…", "en": "Writing secure boot config…"},
    "msg_secure_done": {"zh": "安全启动状态：{state}", "en": "Secure boot status: {state}"},
    "msg_secure_set": {"zh": "安全启动已设置（槽 {slot}），设备将重启", "en": "Secure boot set (slot {slot}); device will reboot"},
    "msg_no_data": {"zh": "（无数据）", "en": "(no data)"},

    "err_bootkey_range": {"zh": "启动密钥槽必须在 0-15 之间", "en": "Boot key slot must be between 0 and 15"},
    "err_secure_unavailable": {"zh": "安全启动不可用（设备未返回数据）", "en": "Secure boot unavailable (device returned no data)"},
    "err_usb_product_long": {"zh": "USB 产品名过长（最多 31 字符）", "en": "USB product name too long (31 chars max)"},

    # ------------------------------------------------------------ diagnostics
    "diag_preload_title": {"zh": "Java 类预加载", "en": "Java class preload"},
    "diag_preload_ok": {"zh": "全部就绪（可在子线程使用 USB）", "en": "All ready (USB usable from worker threads)"},
    "diag_preload_missing": {"zh": "缺失：{names}", "en": "Missing: {names}"},
})


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
