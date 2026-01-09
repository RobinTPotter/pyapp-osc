from kivy.config import Config
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.core.window import Window
import pythonosc

Config.set('kivy','pause_on_minimize', 1)
Window.clearcolor = (1, 1, 1, 1)

class OSC(App):
    def build(self):
        from pythonosc.udp_client import SimpleUDPClient
        c = SimpleUDPClient("192.168.1.174", 57120)
        c.send_message("/voice/sine", "")

if __name__=="__main__":
    OSC().run()
