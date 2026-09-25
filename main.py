"""
PicoKey Manager for Android - Kivy front-end.

Only three things live here: a device picker, a device/operations screen and a
log screen. Every USB operation runs in a worker thread and reports back
through Clock, because blocking the Kivy thread freezes the UI (and Android
would kill an unresponsive app).
"""

from __future__ import annotations

import threading
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform

from picokeyapp import detect, usbhost
from picokeyapp.pk import PicoKey, PhyData, PhyUsbItf, PhyLedDriver

KV = """
<MenuButton@Button>:
    size_hint_y: None
    height: dp(52)
    font_size: '16sp'

<FieldLabel@Label>:
    size_hint_x: 0.42
    halign: 'left'
    valign: 'center'
    text_size: self.size
    font_size: '14sp'
    color: 0.85, 0.87, 0.9, 1

<Row@BoxLayout>:
    size_hint_y: None
    height: dp(44)
    spacing: dp(6)

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
        Label:
            text: 'PicoKey Manager'
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
            text: '扫描 USB 设备'
            on_release: app.scan()
        ScrollView:
            GridLayout:
                id: list_box
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)
        MenuButton:
            text: '运行协议自检（无需硬件）'
            on_release: app.selftest()
        MenuButton:
            text: '查看日志'
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
            height: dp(150)
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
                    text: '重新读取设备信息'
                    on_release: app.refresh()
                MenuButton:
                    text: '读取 PHY 配置'
                    on_release: app.read_phy()
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: 'VID (hex)'
                    TextInput:
                        id: vid
                        multiline: False
                        input_filter: 'int'
                        font_size: '15sp'
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: 'PID (hex)'
                    TextInput:
                        id: pid
                        multiline: False
                        input_filter: 'int'
                        font_size: '15sp'
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: 'LED GPIO'
                    TextInput:
                        id: led_gpio
                        multiline: False
                        input_filter: 'int'
                        font_size: '15sp'
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: 'LED 亮度 (0-255)'
                    TextInput:
                        id: led_btness
                        multiline: False
                        input_filter: 'int'
                        font_size: '15sp'
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    FieldLabel:
                        text: 'LED 驱动'
                    Spinner:
                        id: led_driver
                        values: ['PICO', 'PIMORONI', 'WS2812', 'CYW43', 'NEOPIXEL', 'NONE']
                        text: 'PICO'
                        font_size: '15sp'
                GridLayout:
                    cols: 4
                    size_hint_y: None
                    height: dp(44)
                    ToggleButton:
                        id: itf_ccid
                        text: 'CCID'
                        state: 'down'
                    ToggleButton:
                        id: itf_wcid
                        text: 'WCID'
                        state: 'down'
                    ToggleButton:
                        id: itf_hid
                        text: 'HID'
                        state: 'down'
                    ToggleButton:
                        id: itf_kb
                        text: 'KB'
                MenuButton:
                    text: '写入 PHY 配置（会重启设备）'
                    on_release: app.write_phy()
                MenuButton:
                    text: 'WINK：让 LED 闪一下（FIDO）'
                    on_release: app.wink()
                MenuButton:
                    text: '重启设备'
                    on_release: app.reboot(False)
                MenuButton:
                    text: '重启到 BOOTSEL（拖固件用）'
                    on_release: app.reboot(True)
                MenuButton:
                    text: '断开连接'
                    on_release: app.disconnect()
                MenuButton:
                    text: '返回扫描页'
                    on_release: app.go('scan')
                MenuButton:
                    text: '查看日志'
                    on_release: app.go('log')

<LogScreen>:
    name: 'log'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(8)
        Label:
            text: '日志 / APDU'
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
            text: '清空'
            on_release: app.clear_log()
        MenuButton:
            text: '返回'
            on_release: app.go('device' if app.connected else 'scan')
"""


class ScanScreen(Screen):
    pass


class DeviceScreen(Screen):
    pass


class LogScreen(Screen):
    pass


class PicoKeyApp(App):
    status_text = StringProperty("把 PicoKey 用 OTG 转接线插到手机上，然后点“扫描”。")
    device_text = StringProperty("未连接")
    log_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connected = False
        self.kind = None            # 'apdu' | 'ctap'
        self.transport = None
        self.pk = None
        self.channel = None
        self._channels = []
        self._busy = False

    # ------------------------------------------------------------ plumbing

    def build(self):
        self.title = "PicoKey Manager"
        return Builder.load_string(KV)

    def log(self, msg: str):
        self.log_text += f"{msg}\n"
        if len(self.log_text) > 20000:
            self.log_text = self.log_text[-20000:]

    def clear_log(self):
        self.log_text = ""

    def go(self, name: str):
        self.root.current = name

    def _worker(self, fn, on_ok=None, busy_text="处理中…"):
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
        self.status_text = busy_text
        threading.Thread(target=run, daemon=True).start()

    def _fail(self, exc, tb):
        self._busy = False
        self.log(f"[错误] {exc}")
        self.log(tb)
        self.status_text = f"失败：{exc}"

    def _done(self, text=None):
        self._busy = False
        if text:
            self.status_text = text

    # --------------------------------------------------------------- scan

    def scan(self):
        def work():
            if platform != "android":
                raise RuntimeError("USB Host 只在安卓真机上可用（当前：%s）" % platform)
            channels = detect.scan()
            self._channels = channels
            return channels

        def done(channels):
            self._done()
            box = self.root.get_screen("scan").ids.list_box
            box.clear_widgets()
            if not channels:
                self.status_text = "没找到可用设备。检查 OTG 线和供电；也可以点“查看日志”。"
                box.add_widget(Label(text="（无设备）", size_hint_y=None, height=40))
                return
            self.status_text = f"找到 {len(channels)} 个通道，点一个连接："
            for ch in channels:
                btn = Button(text=f"{ch.label}\n{ch.detail}",
                             size_hint_y=None, height=70, font_size="13sp",
                             halign="center")
                btn.bind(on_release=lambda _b, c=ch: self.connect(c))
                box.add_widget(btn)

        self._worker(work, done, "扫描中…")

    def connect(self, channel):
        def work():
            kind, transport = detect.connect(channel)
            self.kind = kind
            self.transport = transport
            self.channel = channel
            if kind == "apdu":
                self.pk = PicoKey(transport,
                                  connection_type=getattr(transport, "connection_type", 0))
                return ("apdu", self.pk.summary())
            info = {}
            transport.init()
            try:
                info = transport.get_info()
            except Exception as e:
                self.log(f"getInfo 失败：{e}")
            return ("ctap", {"init": transport._init_response, "info": info})

        def done(result):
            self._done("已连接")
            self.connected = True
            kind, payload = result
            if kind == "apdu":
                self.device_text = (
                    f"平台：{payload['platform']}\n"
                    f"产品：{payload['product']}\n"
                    f"版本：{payload['version']}\n"
                    f"通道：{payload['connection']}\n"
                    f"（点“重新读取设备信息”可看 Flash 用量）")
            else:
                init = payload["init"] or {}
                caps = self.transport.capabilities
                self.device_text = (
                    f"通道：FIDO HID (CTAPHID)\n"
                    f"协议版本：{init.get('protocol_version')}\n"
                    f"设备版本：{init.get('device_version')}\n"
                    f"能力：wink={caps.get('wink')} cbor={caps.get('cbor')}\n"
                    f"CID：0x{init.get('cid', 0):08X}")
                self.log("getInfo: " + str(payload["info"]))
            self.log(f"已连接：{channel.label}")
            self.go("device")

        self._worker(work, done, "连接中（手机上要允许 USB 权限）…")

    # ----------------------------------------------------------- device ops

    def _require_apdu(self):
        if self.kind != "apdu" or self.pk is None:
            raise RuntimeError("当前通道不支持 APDU（这是 FIDO HID 通道）")
        return self.pk

    def refresh(self):
        def work():
            pk = self._require_apdu()
            pk = PicoKey(pk.device, connection_type=pk.connection_type)
            self.pk = pk
            flash = pk.flash_info()
            return pk.summary(), flash

        def done(result):
            self._done("已刷新")
            summary, flash = result
            self.device_text = (
                f"平台：{summary['platform']}\n"
                f"产品：{summary['product']}\n"
                f"版本：{summary['version']}\n"
                f"通道：{summary['connection']}\n"
                f"Flash：已用 {flash['used']/1024:.1f}KB / "
                f"共 {flash['total']/1024:.1f}KB，剩余 {flash['free']/1024:.1f}KB\n"
                f"文件数：{flash['nfiles']}，固件：{flash['size']/1024:.1f}KB")
            self.log("flash: " + str(flash))

        self._worker(work, done, "读取中…")

    def read_phy(self):
        def work():
            pk = self._require_apdu()
            phy = pk.phy()
            if phy is None:
                raise RuntimeError("读取 PHY 失败")
            return phy

        def done(phy):
            self._done("PHY 已读取")
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

            def hex4(v):
                return f"{v:04X}" if v is not None else "—"
            self.status_text = (f"PHY 已读取：VID={hex4(phy.vid)} PID={hex4(phy.pid)} "
                                f"LED_GPIO={phy.led_gpio} 亮度={phy.led_brightness}")

        self._worker(work, done, "读取 PHY…")

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
            phy = self._build_phy()
            data = phy.serialize()
            self.log("PHY -> " + data.hex())
            pk.phy(data)
            return data

        def done(data):
            self._done("PHY 已写入，设备正在重启")
            self.log("PHY 写入完成，重新插拔或重新扫描即可连回。")

        self._worker(work, done, "写入 PHY…")

    def wink(self):
        def work():
            if self.kind != "ctap":
                raise RuntimeError("WINK 只在 FIDO HID 通道可用")
            self.transport.wink()
            return True

        def done(_):
            self._done("已发送 WINK，看设备 LED")

        self._worker(work, done, "发送 WINK…")

    def reboot(self, bootsel: bool):
        def work():
            pk = self._require_apdu()
            pk.reboot(bootsel)
            return True

        def done(_):
            self._done("已发送重启命令")
            self.disconnect()

        self._worker(work, done, "重启中…")

    def disconnect(self):
        try:
            if self.pk:
                self.pk.close()
            if self.transport:
                self.transport.close()
        except Exception as e:
            self.log(f"关闭时出错：{e}")
        self.pk = None
        self.transport = None
        self.kind = None
        self.connected = False
        self.device_text = "未连接"
        self.status_text = "已断开"
        self.go("scan")

    # ------------------------------------------------------------ selftest

    def selftest(self):
        def work():
            from picokeyapp import selftest
            return selftest.run()

        def done(report):
            self._done("自检完成，详见日志")
            self.log(report)
            self.go("log")

        self._worker(work, done, "自检中…")


def main():
    PicoKeyApp().run()


if __name__ == "__main__":
    main()
