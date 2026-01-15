from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from osc_build import send_osc_blank, send_osc_float
from threading import Thread

class OSC(App):
    def build(self):
        self.ip = "192.168.1.174"
        self.port = 57120

        root = BoxLayout(orientation="vertical")

        very_top = BoxLayout(orientation="horizontal", size_hint_y=0.05)
        self.ip_text = TextInput(text=self.ip, multiline=False)
        self.port_text = TextInput(text=str(self.port), multiline=False)
        setme = Button(text="Set")
        setme.bind(on_press=self.set_connect)

        very_top.add_widget(self.ip_text)
        very_top.add_widget(self.port_text)
        very_top.add_widget(setme)
        root.add_widget(very_top)


        top = BoxLayout(orientation="horizontal", size_hint_y=0.6)
        b1 = Button(text="/voice")
        b1.bind(on_press=self.on_button)
        b2 = Button(text="/voice/saw")
        b2.bind(on_press=self.on_button)
        top.add_widget(b1)
        top.add_widget(b2)
        bottom = GridLayout(cols=4, rows=4, size_hint_y=0.4) #, spacing=5, padding=5)
        for i in range(14):
            b = Button(text=f"B{i}")
            b.bind(on_press=self.on_button)
            bottom.add_widget(b)

        for i in range(2):
            bottom.add_widget(Widget())

        root.add_widget(top)
        root.add_widget(bottom)
        return root

    def set_connect(self, button):
        try:
            self.ip = self.ip_text.text
            self.port = int(self.port_text.text)
            print(f"set {self.ip} {self.port}")
        except:
            button.background_normal = ""
            button.background_color = [1,0,0,1]

    def on_button(self, button):
        try:
            print(f"hi {button.text}")
#            o = oscAPI.sendMsg(f"{button.text}", dataArray=[""], ipAddr=self.ip, port=self.port)
            Thread(
                target = send_osc_blank,
                args = (self.ip, self.port, button.text), #, [""]),
                daemon=True,
            ).start()
            #print(o)
        except:
            button.background_normal = ""
            button.background_color = [1,0,0,1]

#s    def connect(self, ip="0.0.0.0", port=8080):
#        from pythonosc.udp_client import SimpleUDPClient
#        self.c = SimpleUDPClient(ip, port)
#        print(self.c)


if __name__ == '__main__':
    OSC().run()

 
