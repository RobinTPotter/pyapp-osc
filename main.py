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



import os
import shutil
from kivy.utils import platform

Logger.info(f"platform {platform}")


# We wrap the Android import so the desktop version doesn't crash
if platform == 'android':
    from androidstorage4kivy import SharedStorage, Chooser



try:
    from android.storage import primary_external_storage_path
    Logger.info("imported for android storage")
except:
    Logger.info("non android storage")
    def primary_external_storage_path():
        import os
        if not os.path.exists("./Download"): os.mkdir("./Download")
        return "./"

try:
    from plyer import vibrator
    can_vibrate = True
except Exception as e:
    Logger.info(f"no vibrate {e}")
    can_vibrate = False

class OSC(App):



    def trigger_import(self, value):
        """Call this from your 'Import' button."""
        Logger.info(f"trigger_import {value}")
        if platform == 'android':
            # 📱 Android SAF logic
            ss = Chooser()
            ss.choose_content(on_finished=self.handle_android_selection)
        else:
            # 🖥️ Desktop Path logic
            from plyer import filechooser
            filechooser.open_file(on_selection=self.handle_desktop_selection)

    def handle_android_selection(self, uri_list):
        """Callback for androidstorage4kivy."""
        if uri_list:
            ss = SharedStorage()
            # Get a temporary file path from the URI
            temp_path = ss.get_cache_path(uri_list[0])
            self.finalize_import(temp_path)

    def handle_desktop_selection(self, selection):
        """Callback for plyer filechooser."""
        if selection:
            self.finalize_import(selection[0])

    def old_finalize_import(self, source_path):
        """The final step that overwrites the config and reloads."""
        try:
            # Overwrite the 'bulletproof' internal config
            shutil.copyfile(source_path, self.config_file)

            # Now trigger your existing reload
            self.get_config() 
            # Re-initialize your UI components here
            print("Config updated and reloaded!")
        except Exception as e:
            print(f"Error during import: {e}")

    def finalize_import(self, source_path):
        """Overwrites internal config and triggers your existing rebuild."""
        try:
            # 1. Overwrite your 'bulletproof' internal .ini file
            shutil.copyfile(source_path, self.config_file)

            # 2. Trigger your existing logic to re-read and re-draw
            self.rebuild_ui() 
            print("Import successful: UI reloaded.")
        except Exception as e:
            print(f"Import failed: {e}")





    def on_pause(self):
        Logger.info("pause called")
        return True

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
        # Internal storage - bulletproof
        return os.path.join(self.user_data_dir, "osc_config.ini")

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
        s._companion.text=f"{s._param} {s.value}"
        s._companion._message=f"/param {s._param} {s.value}"
        # see below
        s._companion._was_clicked = False
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
        b.padding = dp(10)

        def bs(button, size):
            button.text_size = size

        b.bind(size=bs)

        b.bind(on_press=self.on_button)
        b._message = b.text
        s._param = param
        b._param = f"/param {param} {min} {max} {value}" # yes, i know this is how it arrived
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

        very_top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28)
        )

        self.ip_text = TextInput(text=str(self.ip).strip(), multiline=False, size_hint_x=5, halign="center")
        self.ip_text.height = self.ip_text.line_height
        self.port_text = TextInput(text=str(self.port).strip(), multiline=False, size_hint_x=2, halign="center")
        self.port_text.height = self.port_text.line_height
        setme = Button(text="Set")
        setme.bind(on_press=self.set_connect)

        export_btn = Button(text="E", size_hint_x=0.5) # or "Export" 
        export_btn.bind(on_press=self.export_config) 
        import_btn = Button(text="I", size_hint_x=0.5) # or "Import"
        import_btn.bind(on_press=self.trigger_import)

        very_top.add_widget(self.ip_text) 
        very_top.add_widget(self.port_text) 
        very_top.add_widget(setme) 
        very_top.add_widget(import_btn) 
        very_top.add_widget(export_btn) 
        self.root.add_widget(very_top) 
        Logger.info("very_top set up")

        top_carousel = Carousel(direction='right', size_hint_y=0.6, )

        top = GridLayout(cols=2, rows=4, spacing=5, padding=2)
        for n in range(8):
            txt = self.hey(self.texts)
            if len(txt)==0:
                top.add_widget(Widget())
            else:
                b1 = Button(text=txt)
                b1._message = b1.text
                b1.bind(on_press=self.on_button)
                top.add_widget(b1)

        top_carousel.add_widget(top)

        param_groups = []
        params = [p for p in self.params]
        i = [elem[0] for elem in enumerate(params) if str(elem[1][0]).startswith("#")]
        Logger.info(f"param splits {i}")
        # get the difference rather than the "running total"
        if len(i)>1:
            i = [i[0]] + [ii[1]-i[ii[0]-1]-1 for ii in enumerate(i) if ii[0]>0]

        if len(i)>0:
            for ii in i:
                hello = params[:ii]
                param_groups.append(hello)
                del params[:ii+1]

            param_groups.append(params)
        else:
            param_groups.append(params)

        Logger.info(param_groups)

        for params in param_groups:
            top2 = BoxLayout(orientation="vertical")
            while len(params)>0:
                p = params.pop(0)
                _, param, mn, mx, v = p
                top2.add_widget(self.doslider(param, min=float(mn), max=float(mx), value=float(v)))

            top_carousel.add_widget(top2)

        self.root.add_widget(top_carousel)
        Logger.info("top set up")

        bottom = GridLayout(cols=4, rows=5, size_hint_y=0.4, spacing=5, padding=2)
        for i in range(20):
            t = self.hey(self.texts)
            if len(t)>0:
                b = Button(text=t)
                b._message = t
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



    def set_connect(self, button):
        try:
            self.ip = self.ip_text.text
            self.port = int(self.port_text.text)
            Logger.info(f"set {self.ip} {self.port}")
            self.rewrite_config()

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
        was_clicked = getattr(button, "_was_clicked", True)

        try:
            Logger.info(f"hi {button.text}")
            msg = button._message.split()
            address = msg.pop(0)
            msg.insert(0,"pressed")
            Thread(
                target = send_osc,
                args = (self.ip, self.port, address, msg),
                daemon=True,
            ).start()
            if can_vibrate: vibrator.vibrate(0.075)
            is_param = getattr(button, "_param", None)
            Logger.info(f"is_param {is_param}")
            if is_param and was_clicked:
                self.rewrite_config([(is_param, msg[-1])])

        except Exception as e:
            Logger.error(f"button down: {e}")
            button.background_normal = ""
            button.background_color = [1,0,0,1]

        if not was_clicked:
            button._was_clicked = True

    def rewrite_config(self, overwrites=[]):
            Logger.info("Rewriting config")

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
                    d = str(d).strip()
                    for o in overwrites:
                        if o[0].split()[1] in d:
                            d = f"{' '.join(o[0].split()[:-1])} {o[1]}"
                    print(f"Writing: {d}")
                    f.write(f"{d}\n")

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


    def export_config(self, button):
        """Export config to Download folder with timestamp"""
        try:
            import shutil
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_path = primary_external_storage_path() + f"/Download/osc_config_{timestamp}.ini"

            shutil.copy(self.config_file, download_path)
            Logger.info(f"Exported to {download_path}")

            # Visual feedback
            button.text = "✓"
            Clock.schedule_once(lambda dt: setattr(button, 'text', '↓'), 1.5)
            if can_vibrate: vibrator.vibrate(0.1)

        except Exception as e:
            Logger.error(f"Export failed: {e}")
            button.background_color = [1,0,0,1]

    def import_config(self, button):
        """Import config using file picker"""
        try:
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self.handle_import,
                filters=["*.ini"]
            )
        except Exception as e:
            Logger.error(f"Import picker failed: {e}")
            button.background_color = [1,0,0,1]

    def handle_import(self, selection):
        """Handle selected file from picker"""
        if selection:
            try:
                import shutil
                shutil.copy(selection[0], self.config_file)
                Logger.info(f"Imported from {selection[0]}")
                self.rebuild_ui(0)
                if can_vibrate: vibrator.vibrate(0.1)
            except Exception as e:
                Logger.error(f"Import copy failed: {e}")


if __name__ == '__main__':
    OSC().run()

