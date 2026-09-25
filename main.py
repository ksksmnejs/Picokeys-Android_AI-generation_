"""
PicoKey Manager for Android - Kivy front-end.

Only three things live here: a device picker, a device/operations screen and a
log screen. Every USB operation runs in a worker thread and reports back
through Clock, because blocking the Kivy thread freezes the UI (and Android
would kill an unresponsive app).

Localisation
------------
All visible text goes through picokeyapp.i18n.t(). The screen KV is a template
with @@key@@ placeholders substituted at build time, so switching language is
just a matter of rebuilding the widget tree - no per-widget bookkeeping.
Static widget rules live in KV_RULES and are loaded once, otherwise every
rebuild would re-declare the dynamic classes (MenuButton, FieldLabel, ...).

The CJK font is registered before anything is drawn (see fonts.py): Kivy's
bundled Roboto has no Chinese glyphs, which is why the first release showed
tofu boxes on a phone.
"""

from __future__ import annotations

import json
import os
import re
import threading
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform

from picokeyapp import detect, fonts, i18n, usbhost
from picokeyapp.pk import PicoKey, PhyData, PhyLedDriver, PhyUsbItf

_PLACEHOLDER = re.compile(r"@@([a-z_0-9]+)@@")
_SETTINGS_FILE = "ui_settings.json"

# ---------------------------------------------------------------------------
# Static rules, loaded exactly once. No translatable text lives here.
# Every widget defaults to the bundled CJK font; without it Chinese labels
# render as tofu boxes because Roboto has no CJK glyphs.
# ---------------------------------------------------------------------------
KV_RULES = """
<Label>:
    font_name: 'AppFont'

<TextInput>:
    font_name: 'AppFont'
    font_size: '15sp'

<MenuButton@Button>:
    font_name: 'AppFont'
    size_hint_y: None
    height: dp(52)
    font_size: '16sp'

<FieldLabel@Label>:
    font_name: 'AppFont'
    size_hint_x: 0.42
    halign: 'left'
    valign: 'center'
    text_size: self.size
    font_size: '14sp'
    color: 0.85, 0.87, 0.9, 1

<Row@BoxLayout>:
    font_name: 'AppFont'
    size_hint_y: None
    height: dp(44)
    spacing: dp(6)
"""

# ---------------------------------------------------------------------------
# Screens. @@key@@ placeholders are replaced by _kv() with the current
# language's string; this block is rebuilt whenever the language changes.
# ---------------------------------------------------------------------------
KV_TEMPLATE = """
ScreenManager:
    ScanScreen:
    DeviceScreen:
    LogScreen:

<ScanScreen>:
    name: 'scan'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(10)
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            spacing: dp(6)
            Label:
                text: '@@language@@'
                size_hint_x: 0.32
                halign: 'left'
                text_size: self.size
                font_size: '15sp'
            Spinner:
                id: lang_spinner
                values: app.lang_values
                text: app.lang_current
                font_name: 'AppFont'
                font_size: '15sp'
                on_text: app.on_lang_change(self.text)
        Label:
            text: '@@app_title@@'
            font_size: '22sp'
            bold: True
            size_hint_y: None
            height: dp(40)
        Label:
            id: status
            text: app.status_text
            size_hint_y: None
            height: dp(60)
            text_size: self.width, None
            shorten: False
            font_size: '14sp'
            color: 0.7, 0.75, 0.8, 1
        MenuButton:
            text: '@@btn_scan@@'
            on_release: app.scan()
        ScrollView:
            GridLayout:
                id: list_box
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)
        MenuButton:
            text: '@@btn_selftest@@'
            on_release: app.selftest()
        MenuButton:
            text: '@@btn_logs@@'
            on_release: app.go('log')

<DeviceScreen>:
    name: 'device'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(8)
        Label:
            id: info
            text: app.device_text
            size_hint_y: None
            height: dp(170)
            text_size: self.width, None
            font_size: '15sp'
            halign: 'left'
            valign: 'top'
        ScrollView:
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)
                padding: 0, dp(6)
                MenuButton:
                    text: '@@btn_refresh@@'
                    on_release: app.refresh()
                MenuButton:
                    text: '@@btn_read_phy@@'
                    on_release: app.read_phy()
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: '@@field_vid@@'
                    TextInput:
                        id: vid
                        multiline: False
                        input_filter: 'int'
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: '@@field_pid@@'
                    TextInput:
                        id: pid
                        multiline: False
                        input_filter: 'int'
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: '@@field_led_gpio@@'
                    TextInput:
                        id: led_gpio
                        multiline: False
                        input_filter: 'int'
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: '@@field_led_btness@@'
                    TextInput:
                        id: led_btness
                        multiline: False
                        input_filter: 'int'
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: '@@field_led_driver@@'
                    Spinner:
                        id: led_driver
                        values: ['PICO', 'PIMORONI', 'WS2812', 'CYW43', 'NEOPIXEL', 'NONE']
                        text: 'PICO'
                        font_name: 'AppFont'
                        font_size: '15sp'
                GridLayout:
                    cols: 4
                    size_hint_y: None
                    height: dp(44)
                    ToggleButton:
                        id: itf_ccid
                        font_name: 'AppFont'
                        text: 'CCID'
                        state: 'down'
                    ToggleButton:
                        id: itf_wcid
                        font_name: 'AppFont'
                        text: 'WCID'
                        state: 'down'
                    ToggleButton:
                        id: itf_hid
                        font_name: 'AppFont'
                        text: 'HID'
                        state: 'down'
                    ToggleButton:
                        id: itf_kb
                        font_name: 'AppFont'
                        text: 'KB'
                MenuButton:
                    text: '@@btn_write_phy@@'
                    on_release: app.write_phy()
                MenuButton:
                    text: '@@btn_wink@@'
                    on_release: app.wink()
                MenuButton:
                    text: '@@btn_reboot@@'
                    on_release: app.reboot(False)
                MenuButton:
                    text: '@@btn_reboot_bootsel@@'
                    on_release: app.reboot(True)
                MenuButton:
                    text: '@@btn_disconnect@@'
                    on_release: app.disconnect()
                MenuButton:
                    text: '@@btn_back_scan@@'
                    on_release: app.go('scan')
                MenuButton:
                    text: '@@btn_logs@@'
                    on_release: app.go('log')

<LogScreen>:
    name: 'log'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(8)
        Label:
            text: '@@log_title@@'
            font_size: '20sp'
            size_hint_y: None
            height: dp(36)
        ScrollView:
            Label:
                id: logview
                text: app.log_text
                size_hint_y: None
                height: max(self.texture_size[1], dp(400))
                text_size: self.width, None
                font_size: '12sp'
                halign: 'left'
                valign: 'top'
                color: 0.8, 0.85, 0.9, 1
        MenuButton:
            text: '@@btn_clear@@'
            on_release: app.clear_log()
        MenuButton:
            text: '@@btn_back@@'
            on_release: app.go('device' if app.connected else 'scan')
"""


class ScanScreen(Screen):
    pass


class DeviceScreen(Screen):
    pass


class LogScreen(Screen):
    pass


def _kv_escape(text: str) -> str:
    """Make a translated string safe inside a KV single-quoted literal."""
    return text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")


class PicoKeyApp(App):
    status_text = StringProperty("")
    device_text = StringProperty("")
    log_text = StringProperty("")
    lang_values = ListProperty([i18n.LANG_NAMES[c] for c in i18n.LANGS])
    lang_current = StringProperty(i18n.LANG_NAMES[i18n.DEFAULT_LANG])
    connected = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = i18n.t("app_title")
        self.kind = None               # 'apdu' | 'ctap'
        self.transport = None
        self.pk = None
        self.channel = None
        self._channels = []
        self._busy = False
        self._switching_lang = False
        self._loaded_kv = None
        self._rules_loaded = False
        # structured device data, so the info block can be re-rendered when the
        # language changes without talking to the device again
        self._dev = None

    # ------------------------------------------------------------ plumbing

    def build(self):
        # Must happen before any widget exists, otherwise the first labels are
        # laid out with Roboto and never re-measure.
        if not fonts.register():
            self._font_warning = True
        self._load_language()
        self.status_text = i18n.t("scan_intro")
        self.device_text = i18n.t("not_connected")
        return self._load_kv()

    def _kv(self) -> str:
        def rep(match):
            return _kv_escape(i18n.t(match.group(1)))

        return _PLACEHOLDER.sub(rep, KV_TEMPLATE)

    def _load_kv(self):
        """Build the widget tree for the current language."""
        if not self._rules_loaded:
            Builder.load_string(KV_RULES)
            self._rules_loaded = True
        kv = self._kv()
        if self._loaded_kv:
            try:
                Builder.unload_string(self._loaded_kv)
            except Exception:
                pass
        self._loaded_kv = kv
        return Builder.load_string(kv)

    # ----------------------------------------------------------- language

    def _settings_path(self) -> str:
        try:
            folder = self.user_data_dir
            os.makedirs(folder, exist_ok=True)
            return os.path.join(folder, _SETTINGS_FILE)
        except Exception:
            return _SETTINGS_FILE

    def _load_language(self):
        try:
            with open(self._settings_path(), "r", encoding="utf-8") as fh:
                code = json.load(fh).get("language")
            if code in i18n.LANGS:
                i18n.set_lang(code)
        except Exception:
            pass
        self.lang_current = i18n.LANG_NAMES[i18n.get_lang()]
        self.lang_values = [i18n.LANG_NAMES[c] for c in i18n.LANGS]

    def _save_language(self, code: str):
        try:
            with open(self._settings_path(), "w", encoding="utf-8") as fh:
                json.dump({"language": code}, fh)
        except Exception:
            pass

    def on_lang_change(self, display_name: str):
        if self._switching_lang:
            return
        code = None
        for candidate, name in i18n.LANG_NAMES.items():
            if name == display_name:
                code = candidate
                break
        if code is None or code == i18n.get_lang():
            return
        self.set_language(code)

    def set_language(self, code: str):
        """Switch language and rebuild the UI with the new strings."""
        i18n.set_lang(code)
        self._save_language(code)
        self.lang_current = i18n.LANG_NAMES[code]
        self.title = i18n.t("app_title")

        # Re-derive everything that was built from translated text.
        if self._dev is None:
            self.status_text = i18n.t("scan_intro")
        else:
            self.status_text = i18n.t("connected")
        self._render_device_text()

        current = self.root.current if self.root else "scan"
        self._switching_lang = True
        try:
            self.root = self._load_kv()
        finally:
            self._switching_lang = False
        self.root.current = current

        # Repopulate the scan list so its labels use the new language too.
        if current == "scan" and self._channels:
            self._render_channel_list(self._channels)
        self.log(f"[i18n] language -> {code}")

    # --------------------------------------------------------------- log

    def log(self, msg: str):
        self.log_text += f"{msg}\n"
        if len(self.log_text) > 20000:
            self.log_text = self.log_text[-20000:]

    def clear_log(self):
        self.log_text = ""

    def go(self, name: str):
        self.root.current = name

    # -------------------------------------------------------- worker glue

    def _worker(self, fn, on_ok=None, busy_text=None):
        if self._busy:
            return

        def run():
            try:
                result = fn()
            except Exception as exc:
                err, tb = exc, traceback.format_exc()
                # 'exc' is cleared at the end of the except block, so bind it
                # to a local name the deferred callback can safely capture.
                Clock.schedule_once(lambda dt: self._fail(err, tb))
                return
            if on_ok:
                Clock.schedule_once(lambda dt: on_ok(result))

        self._busy = True
        self.status_text = busy_text or i18n.t("msg_processing")
        threading.Thread(target=run, daemon=True).start()

    def _fail(self, exc, tb):
        self._busy = False
        self.log(f"[error] {exc}")
        self.log(tb)
        self.status_text = i18n.t("msg_failed", err=exc)

    def _done(self, text=None):
        self._busy = False
        if text:
            self.status_text = text

    # --------------------------------------------------------------- scan

    def scan(self):
        def work():
            if platform != "android":
                raise RuntimeError(i18n.t("err_not_android", plat=platform))
            channels = detect.scan()
            self._channels = channels
            return channels

        self._worker(work, self._render_channel_list, i18n.t("scanning"))

    def _render_channel_list(self, channels):
        self._done()
        box = self.root.get_screen("scan").ids.list_box
        box.clear_widgets()
        if not channels:
            self.status_text = i18n.t("scan_none_hint")
            box.add_widget(Label(text=i18n.t("scan_none_item"),
                                 font_name=fonts.FONT_NAME,
                                 size_hint_y=None, height=40))
            return
        self.status_text = i18n.t("scan_found", n=len(channels))
        for ch in channels:
            btn = Button(text=f"{ch.label}\n{ch.detail}",
                         font_name=fonts.FONT_NAME,
                         size_hint_y=None, height=70, font_size="13sp",
                         halign="center")
            btn.bind(on_release=lambda _b, c=ch: self.connect(c))
            box.add_widget(btn)

    def connect(self, channel):
        def work():
            kind, transport = detect.connect(channel)
            self.kind = kind
            self.transport = transport
            self.channel = channel
            if kind == "apdu":
                self.pk = PicoKey(transport)
                return {"kind": "apdu", "summary": self.pk.summary(),
                        "flash": self.pk.flash_info()}
            transport.init()
            info = {}
            try:
                info = transport.get_info()
            except Exception as e:
                self.log(i18n.t("msg_getinfo_failed", err=e))
            return {"kind": "ctap", "init": transport._init_response, "info": info}

        def done(result):
            self._dev = result
            self.connected = True
            self._render_device_text()
            self._done(i18n.t("connected"))
            self.log(i18n.t("msg_connected_log", label=self.channel.label))
            if result["kind"] == "ctap":
                self.log("getInfo: " + str(result.get("info")))
            self.go("device")

        self._worker(work, done, i18n.t("connecting"))

    # ----------------------------------------------------- device info text

    def _render_device_text(self):
        """Rebuild the info block from saved data, in the current language."""
        if not self._dev:
            self.device_text = i18n.t("not_connected")
            return
        if self._dev["kind"] == "apdu":
            self.device_text = self._apdu_text()
        else:
            self.device_text = self._ctap_text()

    def _apdu_text(self):
        s = self._dev.get("summary") or {}
        lines = [
            f"{i18n.t('lbl_platform')}：{s.get('platform', '?')}",
            f"{i18n.t('lbl_product')}：{s.get('product', '?')}",
            f"{i18n.t('lbl_version')}：{s.get('version', '?')}",
            f"{i18n.t('lbl_channel')}：{s.get('connection', '?')}",
        ]
        flash = self._dev.get("flash")
        if flash and flash.get("total"):
            kb = lambda v: v / 1024.0
            lines.append(i18n.t("flash_line", used=kb(flash["used"]),
                                total=kb(flash["total"]), free=kb(flash["free"])))
            lines.append(i18n.t("files_line", n=flash["nfiles"],
                                size=kb(flash["size"])))
        return "\n".join(lines)

    def _ctap_text(self):
        init = self._dev.get("init") or {}
        caps = {}
        if self.transport is not None:
            try:
                caps = self.transport.capabilities
            except Exception:
                caps = {}
        dev_ver = init.get("device_version") or (0, 0, 0)
        return "\n".join([
            f"{i18n.t('lbl_channel')}：FIDO HID (CTAPHID)",
            f"{i18n.t('lbl_protocol')}：{init.get('protocol_version')}",
            f"{i18n.t('lbl_device_ver')}：{dev_ver}",
            f"{i18n.t('lbl_caps')}：wink={caps.get('wink')} cbor={caps.get('cbor')}",
            f"{i18n.t('lbl_cid')}：0x{init.get('cid', 0):08X}",
        ])

    # ----------------------------------------------------------- device ops

    def _require_apdu(self):
        if self.kind != "apdu" or self.pk is None:
            raise RuntimeError(i18n.t("err_no_apdu"))
        return self.pk

    def refresh(self):
        def work():
            pk = self._require_apdu()
            pk = PicoKey(pk.device, connection_type=pk.connection_type)
            self.pk = pk
            return {"kind": "apdu", "summary": pk.summary(), "flash": pk.flash_info()}

        def done(result):
            self._dev = result
            self._render_device_text()
            self._done(i18n.t("msg_refreshed"))
            self.log("flash: " + str(result["flash"]))

        self._worker(work, done, i18n.t("msg_reading"))

    def read_phy(self):
        def work():
            pk = self._require_apdu()
            phy = pk.phy()
            if phy is None:
                raise RuntimeError(i18n.t("err_phy_read"))
            return phy

        def done(phy):
            ids = self.root.get_screen("device").ids
            if phy.vid is not None:
                ids.vid.text = f"{phy.vid:04X}"
            if phy.pid is not None:
                ids.pid.text = f"{phy.pid:04X}"
            if phy.led_gpio is not None:
                ids.led_gpio.text = str(phy.led_gpio)
            if phy.led_brightness is not None:
                ids.led_btness.text = str(phy.led_brightness)
            if phy.led_driver is not None:
                try:
                    ids.led_driver.text = PhyLedDriver(phy.led_driver).name
                except Exception:
                    pass
            itf = phy.enabled_usb_itf or 0
            ids.itf_ccid.state = "down" if itf & int(PhyUsbItf.CCID) else "normal"
            ids.itf_wcid.state = "down" if itf & int(PhyUsbItf.WCID) else "normal"
            ids.itf_hid.state = "down" if itf & int(PhyUsbItf.HID) else "normal"
            ids.itf_kb.state = "down" if itf & int(PhyUsbItf.KB) else "normal"
            self.log(f"PHY: {phy!r}")
            self._done(i18n.t("msg_phy_read",
                              vid=(f"{phy.vid:04X}" if phy.vid is not None else "—"),
                              pid=(f"{phy.pid:04X}" if phy.pid is not None else "—"),
                              gpio=phy.led_gpio, btness=phy.led_brightness))

        self._worker(work, done, i18n.t("msg_reading_phy"))

    def _build_phy(self) -> PhyData:
        ids = self.root.get_screen("device").ids
        phy = PhyData()

        def hexval(text):
            text = (text or "").strip()
            return int(text, 16) if text else None

        vid, pid = hexval(ids.vid.text), hexval(ids.pid.text)
        if vid is not None or pid is not None:
            phy.vidpid = bytearray(4)
            if vid is not None:
                phy.vid = vid
            if pid is not None:
                phy.pid = pid
        if ids.led_gpio.text.strip():
            phy.led_gpio = int(ids.led_gpio.text) & 0xFF
        if ids.led_btness.text.strip():
            phy.led_brightness = int(ids.led_btness.text) & 0xFF
        try:
            phy.led_driver = int(PhyLedDriver[ids.led_driver.text])
        except Exception:
            phy.led_driver = None
        itf = 0
        if ids.itf_ccid.state == "down":
            itf |= int(PhyUsbItf.CCID)
        if ids.itf_wcid.state == "down":
            itf |= int(PhyUsbItf.WCID)
        if ids.itf_hid.state == "down":
            itf |= int(PhyUsbItf.HID)
        if ids.itf_kb.state == "down":
            itf |= int(PhyUsbItf.KB)
        phy.enabled_usb_itf = itf
        return phy

    def write_phy(self):
        def work():
            pk = self._require_apdu()
            data = self._build_phy().serialize()
            self.log("PHY -> " + data.hex())
            pk.phy(data)
            return data

        def done(_data):
            self._done(i18n.t("msg_phy_written"))
            self.log(i18n.t("msg_phy_written_log"))

        self._worker(work, done, i18n.t("msg_writing_phy"))

    def wink(self):
        def work():
            if self.kind != "ctap":
                raise RuntimeError(i18n.t("err_no_apdu"))
            self.transport.wink()
            return True

        def done(_):
            self._done(i18n.t("msg_wink_sent"))

        self._worker(work, done, i18n.t("msg_winking"))

    def reboot(self, bootsel: bool):
        def work():
            pk = self._require_apdu()
            pk.reboot(bootsel)
            return True

        def done(_):
            self._done(i18n.t("msg_reboot_sent"))
            self.disconnect(silent=True)

        self._worker(work, done, i18n.t("msg_rebooting"))

    def disconnect(self, silent: bool = False):
        try:
            if self.pk:
                self.pk.close()
            if self.transport:
                self.transport.close()
        except Exception as e:
            self.log(i18n.t("msg_closed_error", err=e))
        self.pk = None
        self.transport = None
        self.kind = None
        self.connected = False
        self._dev = None
        self.device_text = i18n.t("not_connected")
        if not silent:
            self.status_text = i18n.t("msg_disconnected")
            self.go("scan")

    # ------------------------------------------------------------ selftest

    def selftest(self):
        def work():
            from picokeyapp import selftest
            return selftest.run()

        def done(report):
            self._done(i18n.t("msg_selftest_done"))
            self.log(report)
            self.go("log")

        self._worker(work, done, i18n.t("msg_selftest_running"))


def main():
    PicoKeyApp().run()


if __name__ == "__main__":
    main()
