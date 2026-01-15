from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from osc_build import send_osc_blank, send_osc_float
from threading import Thread
from time import time
from kivy.metrics import dp

try:
    from android.storage import primary_external_storage_path
except:
    def primary_external_storage_path():
        return "./"

class OSC(App):

    def hey(self,texts):
        return "" if len(texts)==0 else texts.pop(0)


    def build(self):
        self.get_config()
        self.ip = "192.168.1.174"
        self.port = 57120

        root = BoxLayout(orientation="vertical")

        very_top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30))
        self.ip_text = TextInput(text=self.ip, multiline=False, size_hint_x=5)
        self.port_text = TextInput(text=str(self.port), multiline=False, size_hint_x=2)
        setme = Button(text="Set")
        setme.bind(on_press=self.set_connect)

        very_top.add_widget(self.ip_text)
        very_top.add_widget(self.port_text)
        very_top.add_widget(setme)
        root.add_widget(very_top)


        top = BoxLayout(orientation="horizontal", size_hint_y=0.6)
        b1 = Button(text=self.hey(self.texts))
        b1.bind(on_press=self.on_button)
        b2 = Button(text=self.hey(self.texts))
        b2.bind(on_press=self.on_button)
        top.add_widget(b1)
        top.add_widget(b2)
        bottom = GridLayout(cols=4, rows=4, size_hint_y=0.4) #, spacing=5, padding=5)
        for i in range(16):
            t = self.hey(self.texts)
            if t!="":
                b = Button(text=t)
                b.bind(on_press=self.on_button)
                bottom.add_widget(b)
            else:
                bottom.add_widget(Widget())

        root.add_widget(top)
        root.add_widget(bottom)
        return root

    def on_start(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
        except:
            print("possibly not android")

    def get_config_file(self):
        parent = primary_external_storage_path()
        return parent + "/config.ini" 

    def get_config(self):
        self.config_file = self.get_config_file()

        import os 
        if not os.path.exists(self.config_file):
            print("no config make default")
            with open(self.config_file,"w") as f:
                f.write("\n")
                f.write("/voice/saw\n")
                f.write("/voice/sine\n")
                f.write("/voice/pulse\n")

        with open(self.config_file,"r") as f:
            self.texts = f.readlines()

        print(self.texts)


    def set_connect(self, button):
        try:
            self.ip = self.ip_text.text
            self.port = int(self.port_text.text)
            print(f"set {self.ip} {self.port}")
        except:
            button.background_normal = ""
            button.background_color = [1,0,0,1]

    def on_button(self, button):
        now = time()
        if getattr(button, "_last", 0) + 0.2 > now:
            return

        button._last = now

        try:
            print(f"hi {button.text}")
#            o = oscAPI.sendMsg(f"{button.text}", dataArray=[""], ipAddr=self.ip, port=self.port)
            Thread(
                target = send_osc_blank,
                args = (self.ip, self.port, button.text), #, [""]),
                daemon=True,
            ).start()
            #print(o)
        except Exception as e:
            print(e)
            button.background_normal = ""
            button.background_color = [1,0,0,1]

#s    def connect(self, ip="0.0.0.0", port=8080):
#        from pythonosc.udp_client import SimpleUDPClient
#        self.c = SimpleUDPClient(ip, port)
#        print(self.c)


if __name__ == '__main__':
    OSC().run()

 
