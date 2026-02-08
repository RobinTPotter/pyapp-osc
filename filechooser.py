from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


def open_file(on_selection, title="Select file"):
    chooser = FileChooserListView(
        multiselect=False
    )

    btn_ok = Button(text="Open", size_hint_y=None, height=40)
    btn_cancel = Button(text="Cancel", size_hint_y=None, height=40)

    buttons = BoxLayout(size_hint_y=None, height=40)
    buttons.add_widget(btn_cancel)
    buttons.add_widget(btn_ok)

    layout = BoxLayout(orientation="vertical")
    layout.add_widget(chooser)
    layout.add_widget(buttons)

    popup = Popup(
        title=title,
        content=layout,
        size_hint=(0.9, 0.9),
        auto_dismiss=False,
    )

    def do_open(*_):
        selection = chooser.selection[:]  # list, same as plyer
        popup.dismiss()
        on_selection(selection)

    def do_cancel(*_):
        popup.dismiss()
        on_selection([])

    btn_ok.bind(on_release=do_open)
    btn_cancel.bind(on_release=do_cancel)

    popup.open()
