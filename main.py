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
from jnius import autoclass, cast
from android import activity

from kivy.storage.jsonstore import JsonStore

class SAFHelper:
    def __init__(self):
        self.activity = autoclass('org.kivy.android.PythonActivity').mActivity
        self.Intent = autoclass('android.content.Intent')
        self.Uri = autoclass('android.net.Uri')
        self.request_code = 1001
        self.picked_uri = None
        activity.bind(on_activity_result=self.on_result)

    def ask_for_folder(self):
        """Launch the folder picker."""
        intent = self.Intent(self.Intent.ACTION_OPEN_DOCUMENT_TREE)
        self.activity.startActivityForResult(intent, self.request_code)

    def on_result(self, requestCode, resultCode, intent):
        Logger.info("SAF on result")
        if requestCode == self.request_code and intent:
            uri = intent.getData()
            if not uri:
                return

            flags = (self.Intent.FLAG_GRANT_READ_URI_PERMISSION |
                     self.Intent.FLAG_GRANT_WRITE_URI_PERMISSION)

            self.activity.getContentResolver().takePersistableUriPermission(uri, flags)
            self.picked_uri = uri.toString()

            from kivy.app import App
            app = App.get_running_app()
            if app:
                app.on_storage_ready()


    def old_on_result(self, requestCode, resultCode, intent):
        """Called when folder is picked."""
        if requestCode == self.request_code and intent:
            uri = intent.getData()
            if uri:
                # persist read+write access
                flags = (self.Intent.FLAG_GRANT_READ_URI_PERMISSION |
                         self.Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                self.activity.getContentResolver().takePersistableUriPermission(uri, flags)
                self.picked_uri = uri.toString()

    def has_permission(self):
        """Do we already have a persisted folder URI?"""
        return bool(self.picked_uri)

    def get_uri(self):
        """Return the persisted URI string (if any)."""
        return self.picked_uri

# store for saved SAF folder
saf_store = JsonStore("saf_store.json")
saf = SAFHelper()

DocumentFile = autoclass(
    "androidx.documentfile.provider.DocumentFile"
)
Uri = autoclass("android.net.Uri")


def get_root_document():
    uri = Uri.parse(saf.picked_uri)
    return DocumentFile.fromTreeUri(
        saf.activity,
        uri
    )




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

    storage_ready = False
    ui_built = False

    def on_storage_ready(self):
        if self.storage_ready:
            return

        from kivy.logger import Logger
        Logger.info("SAF storage ready")

        self.storage_ready = True

        if not saf_store.exists("folder"):
            saf_store.put("folder", uri=saf.picked_uri)

        # NOW it is safe to load config
        self.get_config()

        # NOW it is safe to build UI
        self.build_ui()



    def on_pause(self):
        Logger.info("pause called")
        return True

    def on_start(self):
        from kivy.logger import Logger

        if saf_store.exists("folder"):
            saf.picked_uri = saf_store.get("folder")["uri"]

        if not saf.has_permission():
            Logger.info("No SAF folder yet — requesting")
            saf.ask_for_folder()
        else:
            self.on_storage_ready()



    def old_on_start(self):

        try:
            # If we already saved a folder URI, load it
            if saf_store.exists("folder"):
                saf.picked_uri = saf_store.get("folder")["uri"]

            # If no folder yet, ask user to pick one
            if not saf.has_permission():
                saf.ask_for_folder()
            else:
                Logger.info("Already have SAF folder access")

        except Exception as e:
            Logger.info(f"not android storage SAF: {e}")


#        try:
#            from android.permissions import request_permissions, Permission
##            request_permissions([
#                Permission.READ_EXTERNAL_STORAGE,
#                Permission.WRITE_EXTERNAL_STORAGE,
#            ])
#            Logger.info("permissions requested")
#        except:
#            Logger.info("possibly not android")

    def on_resume(self):
        # if SAFHelper got a picked folder, save it
        if saf.picked_uri and not saf_store.exists("folder"):
            saf_store.put("folder", uri=saf.picked_uri)
            Logger.info(f"Saved SAF folder URI: {saf.picked_uri}")

        Clock.schedule_once(self.rebuild_ui, 0.5)


    from jnius import autoclass

    def open_saf_file(self, uri_string, mode="r"):
        """Open a URI from SAF for reading or writing."""
        Uri = autoclass("android.net.Uri").parse(uri_string)
        resolver = saf.activity.getContentResolver()
        stream = resolver.openInputStream(Uri) if "r" in mode else resolver.openOutputStream(Uri, "w")
        return stream

    def get_config_saf_path(self):
        """Return a file-like URI for 'osc_config.ini' in the chosen folder."""
        return saf.get_uri() + "/osc_config.ini"


    def get_config_file(self):
        parent = primary_external_storage_path() + "/Documents"
        return parent + "/osc_config.ini"

    def get_config(self):
        lines = self.read_config()

        if not lines:
            self.write_config(
                "192.168.1.175\n"
                "57120\n"
                "/voice/t0\n"
                "/note 60\n"
            )
            lines = self.read_config()

        self.ip = lines[0]
        self.port = int(lines[1])
        self.texts = [l.strip() for l in lines[2:]]



    def older_get_config(self):
        if not saf.has_permission():
            Logger.error("No shared folder granted yet!")
            return

        cfg_uri = self.get_config_saf_path()

        try:
            # try opening existing
            with self.open_saf_file(cfg_uri, "r") as f:
                lines = f.read().splitlines()
        except Exception:
            # make default
            with self.open_saf_file(cfg_uri, "w") as f:
                f.write("192.168.1.175\n57120\n")
                for b in range(4): f.write(f"/voice/t{b}\n")
                for b in range(16): f.write(f"/note {b+60}\n")
            with self.open_saf_file(cfg_uri, "r") as f:
                lines = f.read().splitlines()

        self.texts = [t.strip() for t in lines[2:]]
        self.ip = lines[0]
        self.port = int(lines[1])


    def get_config_document(self):
        root = get_root_document()

        doc = root.findFile("osc_config.ini")
        if doc:
            return doc

        # create if missing
        return root.createFile(
            "text/plain",
            "osc_config.ini"
        )

    def read_config(self):
        doc = get_config_document()
        resolver = saf.activity.getContentResolver()

        stream = resolver.openInputStream(doc.getUri())
        data = stream.read().decode("utf-8")
        stream.close()

        return data.splitlines()

    def write_config(self,text):
        doc = get_config_document()
        resolver = saf.activity.getContentResolver()

        stream = resolver.openOutputStream(doc.getUri(), "w")
        stream.write(text.encode("utf-8"))
        stream.close()


    def old_get_config(self):
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


#    def on_resume(self):
#        Logger.info("on resume")
#        Clock.schedule_once(self.rebuild_ui, 0.5)

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
        if not self.storage_ready:
            Logger.info("Storage not ready")
            return

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
        very_top.add_widget(self.ip_text)
        very_top.add_widget(self.port_text)
        very_top.add_widget(setme)
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


if __name__ == '__main__':
    OSC().run()

