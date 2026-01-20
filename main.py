import os
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from osc_build import *
from threading import Thread
from time import time
from kivy.metrics import dp
from kivy.uix.carousel import Carousel
from kivy.clock import Clock
from kivy.core.window import Window
import sys
from kivy.logger import Logger

def excepthook(exctype, value, traceback):
    Logger.exception("Uncaught exception", exc_info=(exctype, value, traceback))

sys.excepthook = excepthook

try:
    from android.storage import primary_external_storage_path
    Logger.info("imported for android storage")
except:
    Logger.info("non android storage")
    def primary_external_storage_path():
        import os
        if not os.path.exists("./Documents"): os.mkdir("./Documents")
        return "./"

try:
    from plyer import vibrator
    can_vibrate = True
except Exception as e:
    Logger.info(f"no vibrate {e}")
    can_vibrate = False

class OSC(App):

    def on_pause(self):
        Logger.info("pause called")
        return True

    def on_resume(self):
        Logger.info("on resume")
        Clock.schedule_once(self.rebuild_ui, 0.5)

    def rebuild_ui(self, dt):
        Logger.info(f"rebuild ui {dt}")

        self.get_config()
        self.build_ui()

        Window.canvas.ask_update()

    def hey(self,texts):
        return "" if len(texts)==0 else texts.pop(0)

    def build(self):
        Logger.info("build (initial)")

        self.get_config()

        # ROOT CREATED ONCE
        self.root = BoxLayout(
            orientation="vertical",
            spacing=5,
            padding=5,
        )

        # build UI contents
        self.build_ui()

        return self.root

    def update_slider(self, s, value):
        # callback on slider made by doslider
        s.value = round(value,2)
        s._companion.text=f"/param {s._param} {s.value}"
        # see below
        if not s._init: self.on_button(s._companion)
        s._init = False

    def doslider(self, param, min=0, max=1.0, value=0.5, step=0.1):
        # function to create a slider and button combo, button attached to slider as
        # _companion and _param is the name of the param which goes to the message
        s = Slider(min=min, max=max, value=value, step=step, size_hint_x=5)
        b = Button(size_hint_x=2)
        b.text_size = (b.width, None)
        b.halign = "center"
        b.valign = "middle"

        def bs(button, size):
            button.text_size = size

        b.bind(size=bs)

        b.bind(on_press=self.on_button)
        s._param = param
        s._companion = b
        s.bind(value=self.update_slider)
        s._init = True # flag for stopping on_button from firing for first drawing
        self.update_slider(s, value)
        l = BoxLayout(orientation="horizontal")
        l.add_widget(b)
        l.add_widget(s)
        return l

    def build_ui(self):
        Logger.info("build_ui")

        self.get_config()
        self.root.clear_widgets()

        very_top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30))
        self.ip_text = TextInput(text=str(self.ip).strip(), multiline=False, size_hint_x=5)
        self.port_text = TextInput(text=str(self.port).strip(), multiline=False, size_hint_x=2)
        setme = Button(text="Set")
        setme.bind(on_press=self.set_connect)
        very_top.add_widget(self.ip_text)
        very_top.add_widget(self.port_text)
        very_top.add_widget(setme)
        self.root.add_widget(very_top)
        Logger.info("very_top set up")

        top_carousel = Carousel(direction='right', size_hint_y=0.6, )

        top = GridLayout(cols=2, rows=2, spacing=5, padding=2)
        b1 = Button(text=self.hey(self.texts))
        b1.bind(on_press=self.on_button)
        b2 = Button(text=self.hey(self.texts))
        b2.bind(on_press=self.on_button)
        b3 = Button(text=self.hey(self.texts))
        b3.bind(on_press=self.on_button)
        b4 = Button(text=self.hey(self.texts))
        b4.bind(on_press=self.on_button)
        top.add_widget(b1)
        top.add_widget(b2)
        top.add_widget(b3)
        top.add_widget(b4)
        top_carousel.add_widget(top)


        top2 = BoxLayout(orientation="vertical")
        for p in self.params:
            _, param, mn, mx, v = p
            top2.add_widget(self.doslider(param, min=float(mn), max=float(mx), value=float(v)))

        top_carousel.add_widget(top2)


        self.root.add_widget(top_carousel)
        Logger.info("top set up")

        bottom = GridLayout(cols=4, rows=4, size_hint_y=0.4, spacing=5, padding=2)
        for i in range(16):
            t = self.hey(self.texts)
            if len(t)>0:
                b = Button(text=t)
                b._nodeID = 0
                b.bind(on_press=self.on_button)
                b.bind(on_release=self.on_release_button)
                bottom.add_widget(b)
            else:
                Logger.info("blank")
                bottom.add_widget(Widget())

        self.root.add_widget(bottom)
        Logger.info("bottom set up")

        self.ip = self.ip_text.text
        self.port = int(self.port_text.text)

        return self.root

    def on_start(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
            Logger.info("permissions requested")
        except:
            Logger.info("possibly not android")

    def get_config_file(self):
        parent = primary_external_storage_path() + "/Documents"
        return parent + "/osc_config.ini"

    def get_config(self):
        self.config_file = self.get_config_file()

        if not os.path.exists(self.config_file):
            Logger.info("no config make default")
            with open(self.config_file,"w") as f:
                f.write("192.168.1.175\n")
                f.write("57120\n")
                for b in range(4): f.write(f"/voice/t{b}\n")
                for b in range(16): f.write(f"/note {b+60}\n")
                f.write(f"/param a1 0.0 1.0 0.5\n")
                f.write(f"/param a2 0.0 1.0 0.5\n")
                f.write(f"/param a3 0.0 1.0 0.5\n")
                f.write(f"/param a4 0.0 1.0 0.5\n")
                f.write(f"/param vibrato_freq 0.1 5.0 1.0\n")
                f.write(f"/param vibrato_strength 0.0 1.0 0.5\n")
                f.write(f"/param pulse_width 0.0 1.0 0.5\n")

            Logger.info("written fake config")

        with open(self.config_file,"r") as f:
            self.texts = f.readlines()

        self.ip = self.texts.pop(0)
        self.port = int(self.texts.pop(0))

        inputs = self.texts
        self.texts = [t.strip() for t in inputs if not "/param" in t]
        self.params = [t.strip().split() for t in inputs if "/param" in t] #of the form /param name min max start
        Logger.info(self.texts)


    def set_connect(self, button):
        try:
            self.ip = self.ip_text.text
            self.port = int(self.port_text.text)
            Logger.info(f"set {self.ip} {self.port}")
            with open(self.config_file,"r") as f:
                data = f.readlines()

            data = [t.strip() for t in data]
            data.pop(0)
            data.pop(0)
            data.insert(0, self.port)
            data.insert(0, self.ip)
            Logger.info("writing new port ip")

            with open(self.config_file,"w") as f:
                for d in data:
                    f.write(f"{str(d).strip()}\n")

        except Exception as e:
            Logger.error(e)
            button.background_normal = ""
            button.background_color = [1,0,0,1]

    def on_button(self, button):
        now = time()
        if getattr(button, "_last", 0) + 0.2 > now:
            return

        button._last = now
        button._nodeID = int(time() * 100) % 10 ** 9

        try:
            Logger.info(f"hi {button.text}")
            msg = button.text.split()
            address = msg.pop(0)
            msg.insert(0,"pressed")
            Thread(
                target = send_osc,
                args = (self.ip, self.port, address, msg),
                daemon=True,
            ).start()
            if can_vibrate: vibrator.vibrate(0.075)
        except Exception as e:
            Logger.error(f"button down: {e}")
            button.background_normal = ""
            button.background_color = [1,0,0,1]

    def on_release_button(self, button):
        now = time()
        if getattr(button, "_uplast", 0) + 0.2 > now:
            return

        button._uplast = now
        try:
            Logger.info(f"hi up {button.text}")
            msg = button.text.split()
            address = msg.pop(0)
            msg.insert(0,"release")
            Thread(
                target = send_osc,
                args = (self.ip, self.port, address, msg),
                daemon=True,
            ).start()
        except Exception as e:
            Logger.error(f"button release {e}")
            button.background_normal = ""
            button.background_color = [1,0,0,1]


if __name__ == '__main__':
    OSC().run()

