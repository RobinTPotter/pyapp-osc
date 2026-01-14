from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout



class OSC(App):
    def build(self):
        self.connect("192.168.1.174", 57120)
        root = BoxLayout(orientation="vertical")
        top = BoxLayout(orientation="horizontal", size_hint_y=0.6)
        b1 = Button(text="/voice/sine")
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

    def on_button(self, button):
        print(f"hi {button.text}")
        o = self.c.send_message(f"{button.text}", "")
        print(o)

    def connect(self, ip="0.0.0.0", port=8080):
        from pythonosc.udp_client import SimpleUDPClient
        self.c = SimpleUDPClient(ip, port)


if __name__ == '__main__':
    OSC().run()

