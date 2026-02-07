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

# ============================================================================
# EXCEPTION HANDLING SETUP
# ============================================================================

def excepthook(exctype, value, traceback):
    """
    Custom exception handler that logs uncaught exceptions to Kivy's logger
    instead of crashing silently or printing to stdout
    """
    Logger.exception("Uncaught exception", exc_info=(exctype, value, traceback))

# Replace Python's default exception handler with our custom one
sys.excepthook = excepthook

import shutil
from kivy.utils import platform

Logger.info(f"platform {platform}")

# ============================================================================
# PLATFORM-SPECIFIC IMPORTS
# ============================================================================

# Android storage API - only import on Android to prevent desktop crashes
if platform == 'android':
    from androidstorage4kivy import SharedStorage, Chooser

# Attempt to import Android-specific storage path functionality
try:
    from android.storage import primary_external_storage_path
    Logger.info("imported for android storage")
except:
    Logger.info("non android storage")
    # Fallback for desktop: create and use a local Download folder
    def primary_external_storage_path():
        import os
        if not os.path.exists("./Download"): 
            os.mkdir("./Download")
        return "./"

# Attempt to import vibration functionality (mobile devices)
try:
    from plyer import vibrator
    can_vibrate = True
except Exception as e:
    Logger.info(f"no vibrate {e}")
    can_vibrate = False

# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class OSC(App):
    """
    Main Kivy application for OSC (Open Sound Control) controller.
    Provides a touch interface with buttons and sliders that send OSC messages
    to a specified IP address and port. Configuration is stored in an .ini file.
    """

    # ========================================================================
    # CONFIGURATION MANAGEMENT
    # ========================================================================

    def get_config_file(self):
        """
        Returns the path to the config file stored in internal app storage.
        This location is 'bulletproof' - survives app updates and won't be 
        accidentally deleted by users.
        """
        return os.path.join(self.user_data_dir, "osc_config.ini")

    def get_config(self):
        """
        Reads the configuration file and parses it into instance variables.
        Config format:
        - Line 1: IP address
        - Line 2: Port number
        - Following lines: Button messages (format: /address value)
        - Param lines: Slider definitions (format: /param name min max start)
        
        If config doesn't exist, creates a default one.
        """
        self.config_file = self.get_config_file()

        # Create default config if none exists
        if not os.path.exists(self.config_file):
            Logger.info("no config make default")
            with open(self.config_file, "w") as f:
                # Default IP address
                f.write("192.168.1.175\n")
                # Default port
                f.write("57120\n")
                # Default top buttons (voice triggers)
                for b in range(4): 
                    f.write(f"/voice/t{b}\n")
                # Default note buttons (MIDI notes 60-75)
                for b in range(16): 
                    f.write(f"/note {b+60}\n")
                # Default parameter sliders with min, max, and starting values
                f.write(f"/param a1 0.0 1.0 0.5\n")
                f.write(f"/param a2 0.0 1.0 0.5\n")
                f.write(f"/param a3 0.0 1.0 0.5\n")
                f.write(f"/param a4 0.0 1.0 0.5\n")
                f.write(f"/param vibrato_freq 0.1 5.0 1.0\n")
                f.write(f"/param vibrato_strength 0.0 1.0 0.5\n")
                f.write(f"/param pulse_width 0.0 1.0 0.5\n")
            Logger.info("written fake config")

        # Read and parse the config file
        with open(self.config_file, "r") as f:
            self.texts = f.readlines()

        # Extract IP and port from first two lines
        self.ip = self.texts.pop(0)
        self.port = int(self.texts.pop(0))

        # Separate button messages from parameter definitions
        inputs = self.texts
        # Button messages (don't contain "/param")
        self.texts = [t.strip() for t in inputs if not "/param" in t]
        # Parameter definitions split into [address, name, min, max, start]
        self.params = [t.strip().split() for t in inputs if "/param" in t]
        Logger.info(self.texts)

    def rewrite_config(self, overwrites=[]):
        """
        Rewrites the entire config file, optionally updating parameter values.
        
        Args:
            overwrites: List of tuples (param_definition, new_value) to update
                       specific parameter starting values in the config
        """
        Logger.info("Rewriting config")

        # Read current config
        with open(self.config_file, "r") as f:
            data = f.readlines()

        # Strip whitespace from all lines
        data = [t.strip() for t in data]
        
        # Remove old IP and port
        data.pop(0)
        data.pop(0)
        
        # Insert new IP and port at the beginning
        data.insert(0, self.port)
        data.insert(0, self.ip)
        Logger.info("writing new port ip")

        # Write updated config
        with open(self.config_file, "w") as f:
            for d in data:
                d = str(d).strip()
                # Apply any parameter value overwrites
                for o in overwrites:
                    # If this line matches a parameter to overwrite
                    if o[0].split()[1] in d:
                        # Replace the last value with the new one
                        d = f"{' '.join(o[0].split()[:-1])} {o[1]}"
                print(f"Writing: {d}")
                f.write(f"{d}\n")

    # ========================================================================
    # IMPORT/EXPORT FUNCTIONALITY
    # ========================================================================

    def export_config(self, button):
        """
        Exports the current config file to the Download folder with a timestamp.
        Provides visual feedback by temporarily changing the button text.
        """
        try:
            import shutil
            from datetime import datetime

            # Generate filename with current date/time
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_path = primary_external_storage_path() + f"/Download/osc_config_{timestamp}.ini"

            # Copy config to Download folder
            shutil.copy(self.config_file, download_path)
            Logger.info(f"Exported to {download_path}")

            # Visual feedback: change button text briefly
            button.text = "*"
            Clock.schedule_once(lambda dt: setattr(button, 'text', 'E'), 1.5)
            if can_vibrate: 
                vibrator.vibrate(0.1)

        except Exception as e:
            Logger.error(f"Export failed: {e}")
            button.background_color = [1, 0, 0, 1]

    def trigger_import(self, value):
        """
        Initiates the import process using platform-appropriate file picker.
        On Android: Uses SAF (Storage Access Framework) via androidstorage4kivy
        On Desktop: Uses plyer's filechooser
        """
        Logger.info(f"trigger_import {value}")
        
        if platform == 'android':
            # Android: Use Storage Access Framework
            self.chooser = Chooser(callback=self.handle_android_selection)
            # Trigger the Android file picker UI
            self.chooser.choose_content()
        else:
            # Desktop: Use plyer's file picker
            from plyer import filechooser
            filechooser.open_file(on_selection=self.handle_desktop_selection)

    def handle_android_selection(self, uri_list):
        """
        Callback for Android file selection.
        Copies the selected file from shared storage to private app storage,
        then imports it.
        
        Args:
            uri_list: List of content:// URIs selected by the user
        """
        if not uri_list:
            return

        try:
            ss = SharedStorage()

            # Copy the selected shared file into private app storage
            # This is necessary because content:// URIs can't be opened directly
            private_path = ss.copy_from_shared(uri_list[0])

            if not private_path:
                raise RuntimeError("Failed to copy file from shared storage")

            # Now we have a real file path that Python can open
            self.finalize_import(private_path)

        except Exception as e:
            Logger.exception(f"Android file import failed: {e}")

    def dont_handle_android_selection(self, uri_list):
        """
        UNUSED: Alternative Android selection handler using cache path.
        Left in code but not currently used - the copy_from_shared approach
        is more reliable.
        """
        if uri_list:
            ss = SharedStorage()
            # Get a temporary file path from the URI
            temp_path = ss.get_cache_path(uri_list[0])
            self.finalize_import(temp_path)

    def handle_desktop_selection(self, selection):
        """
        Callback for desktop file selection via plyer.
        
        Args:
            selection: List containing the selected file path
        """
        if selection:
            self.finalize_import(selection[0])

    def finalize_import(self, source_path):
        """
        Completes the import process by copying the selected file over the
        internal config and rebuilding the UI.
        
        Args:
            source_path: Path to the config file to import
        """
        try:
            # Overwrite the internal config file
            shutil.copyfile(source_path, self.config_file)

            # Reload the UI with the new config
            self.rebuild_ui(0)
            print("Import successful: UI reloaded.")
        except Exception as e:
            print(f"Import failed: {e}")

    def import_config(self, button):
        """
        UNUSED: Alternative import method using plyer's filechooser.
        The trigger_import method is used instead.
        """
        try:
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self.handle_import,
                filters=["*.ini"]
            )
        except Exception as e:
            Logger.error(f"Import picker failed: {e}")
            button.background_color = [1, 0, 0, 1]

    def handle_import(self, selection):
        """
        UNUSED: Handler for the import_config method.
        Copies the selected file and rebuilds the UI.
        """
        if selection:
            try:
                import shutil
                shutil.copy(selection[0], self.config_file)
                Logger.info(f"Imported from {selection[0]}")
                self.rebuild_ui(0)
                if can_vibrate: 
                    vibrator.vibrate(0.1)
            except Exception as e:
                Logger.error(f"Import copy failed: {e}")

    # ========================================================================
    # APP LIFECYCLE METHODS
    # ========================================================================

    def on_start(self):
        """
        Called when the app starts. Requests storage permissions on Android.
        """
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
            Logger.info("permissions requested")
        except:
            Logger.info("possibly not android")

    def on_pause(self):
        """
        Called when the app is paused (e.g., user switches to another app).
        Returning True allows the app to pause instead of stopping.
        """
        Logger.info("pause called")
        return True

    def on_resume(self):
        """
        Called when the app resumes from a paused state.
        Schedules a UI rebuild to refresh the display.
        """
        Logger.info("on resume")
        Clock.schedule_once(self.rebuild_ui, 0.5)

    # ========================================================================
    # UI BUILDING AND MANAGEMENT
    # ========================================================================

    def build(self):
        """
        Main Kivy build method - called once when the app starts.
        Creates the root widget and initial UI layout.
        
        Returns:
            BoxLayout: The root widget for the application
        """
        Logger.info("build (initial)")

        # Load configuration
        self.get_config()

        # Create root container (created only once)
        self.root = BoxLayout(
            orientation="vertical",
            spacing=5,
            padding=5,
        )

        # Build the UI contents
        self.build_ui()

        return self.root

    def rebuild_ui(self, dt):
        """
        Rebuilds the entire UI from scratch, typically after config changes.
        
        Args:
            dt: Delta time (required by Kivy's Clock.schedule_once)
        """
        Logger.info(f"rebuild ui {dt}")

        # Reload config from file
        self.get_config()
        
        # Rebuild all UI widgets
        self.build_ui()

        # Force canvas update
        Window.canvas.ask_update()

    def hey(self, texts):
        """
        Helper function to safely pop from a list.
        Returns empty string if list is empty, otherwise pops and returns first item.
        
        Args:
            texts: List to pop from
            
        Returns:
            str: First item from list or empty string
        """
        return "" if len(texts) == 0 else texts.pop(0)

    def build_ui(self):
        """
        Constructs the complete UI layout with three main sections:
        1. Top bar: IP/port configuration and import/export buttons
        2. Middle carousel: Button grid and parameter sliders across multiple pages
        3. Bottom grid: Note/trigger buttons (typically 4x5 grid)
        """
        Logger.info("build_ui")

        # Reload configuration
        self.get_config()
        
        # Clear all existing widgets from root
        self.root.clear_widgets()

        # ====================================================================
        # TOP BAR: Connection settings and import/export
        # ====================================================================
        very_top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28)  # Fixed height in density-independent pixels
        )

        # IP address input field
        self.ip_text = TextInput(
            text=str(self.ip).strip(), 
            multiline=False, 
            size_hint_x=5,  # Takes 5 parts of horizontal space
            halign="center"
        )
        self.ip_text.height = self.ip_text.line_height
        
        # Port number input field
        self.port_text = TextInput(
            text=str(self.port).strip(), 
            multiline=False, 
            size_hint_x=2,  # Takes 2 parts of horizontal space
            halign="center"
        )
        self.port_text.height = self.port_text.line_height
        
        # Button to apply IP/port changes
        setme = Button(text="Set")
        setme.bind(on_press=self.set_connect)

        # Export config button (small, labeled "E")
        export_btn = Button(text="E", size_hint_x=0.5)
        export_btn.bind(on_press=self.export_config)
        
        # Import config button (small, labeled "I")
        import_btn = Button(text="I", size_hint_x=0.5)
        import_btn.bind(on_press=self.trigger_import)

        # Send all sliders button (small, labeled "S")
        send_all_btn = Button(text="S", size_hint_x=0.5)
        send_all_btn.bind(on_press=self.send_all_param)

        # Add all top bar widgets
        very_top.add_widget(self.ip_text)
        very_top.add_widget(self.port_text)
        very_top.add_widget(setme)
        very_top.add_widget(import_btn)
        very_top.add_widget(export_btn)
        self.root.add_widget(very_top)
        Logger.info("very_top set up")

        # ====================================================================
        # MIDDLE CAROUSEL: Button grid and parameter sliders
        # ====================================================================
        top_carousel = Carousel(
            direction='right',  # Swipe right to go to next page
            size_hint_y=0.6,    # Takes 60% of vertical space
        )

        # FIRST PAGE: 2x4 grid of trigger buttons
        top = GridLayout(cols=2, rows=4, spacing=5, padding=2)
        for n in range(8):
            txt = self.hey(self.texts)
            if len(txt) == 0:
                # Empty space if no button defined
                top.add_widget(Widget())
            else:
                # Create button with OSC message
                b1 = Button(text=txt)
                b1._message = b1.text
                b1.bind(on_press=self.on_button)
                top.add_widget(b1)

        top_carousel.add_widget(top)

        # SUBSEQUENT PAGES: Parameter sliders grouped by # markers
        param_groups = []
        params = [p for p in self.params]
        
        # Find indices where lines start with "#" (group separators)
        i = [elem[0] for elem in enumerate(params) if str(elem[1][0]).startswith("#")]
        Logger.info(f"param splits {i}")
        
        # Convert running total indices to group sizes
        if len(i) > 1:
            i = [i[0]] + [ii[1] - i[ii[0] - 1] - 1 for ii in enumerate(i) if ii[0] > 0]

        # Split params into groups based on # markers
        if len(i) > 0:
            for ii in i:
                hello = params[:ii]
                param_groups.append(hello)
                del params[:ii + 1]  # Also delete the # marker line
            param_groups.append(params)  # Add remaining params
        else:
            # No groups, treat all params as one group
            param_groups.append(params)

        Logger.info(param_groups)
        self.all_param_sliders = []
        # Create a carousel page for each parameter group
        for params in param_groups:
            top2 = BoxLayout(orientation="vertical")
            while len(params) > 0:
                p = params.pop(0)
                # Parse parameter definition: /param name min max start_value
                _, param, mn, mx, v = p
                # Create slider for this parameter
                sld = self.doslider(
                    param, 
                    min=float(mn), 
                    max=float(mx), 
                    value=float(v)
                )
                top2.add_widget(sld)
                self.all_param_sliders.append(sld)
            top_carousel.add_widget(top2)

        self.root.add_widget(top_carousel)
        Logger.info("top set up")

        # ====================================================================
        # BOTTOM GRID: Note/trigger buttons (4x5 = 20 buttons)
        # ====================================================================
        bottom = GridLayout(
            cols=4, 
            rows=5, 
            size_hint_y=0.4,  # Takes 40% of vertical space
            spacing=5, 
            padding=2
        )
        
        for i in range(20):
            t = self.hey(self.texts)
            if len(t) > 0:
                # Create button with OSC message
                b = Button(text=t)
                b._message = t
                b._nodeID = 0
                # Bind both press and release events
                b.bind(on_press=self.on_button)
                b.bind(on_release=self.on_release_button)
                bottom.add_widget(b)
            else:
                # Empty space if no button defined
                Logger.info("blank")
                bottom.add_widget(Widget())

        self.root.add_widget(bottom)
        Logger.info("bottom set up")

        # Update IP and port from text inputs
        self.ip = self.ip_text.text
        self.port = int(self.port_text.text)

        return self.root

    # ========================================================================
    # SLIDER CREATION AND MANAGEMENT
    # ========================================================================

    def doslider(self, param, min=0, max=1.0, value=0.5, step=0.1):
        """
        Creates a slider-button combo for parameter control.
        The button displays the parameter name and current value.
        The slider adjusts the value.
        
        Args:
            param: Parameter name
            min: Minimum value
            max: Maximum value
            value: Starting value
            step: Increment step for slider
            
        Returns:
            BoxLayout: Container with button and slider
        """
        # Create slider
        s = Slider(
            min=min, 
            max=max, 
            value=value, 
            step=step, 
            size_hint_x=5  # Slider takes 5 parts of space
        )
        
        # Create companion button
        b = Button(size_hint_x=2)  # Button takes 2 parts of space
        b.text_size = (b.width, None)
        b.halign = "center"
        b.valign = "middle"
        b.padding = dp(10)

        # Update button text size when button is resized
        def bs(button, size):
            button.text_size = size
        b.bind(size=bs)

        # Clicking button sends OSC message with current value
        b.bind(on_press=self.on_button)
        b._message = b.text
        
        # Store parameter info on both widgets
        s._param = param
        b._param = f"/param {param} {min} {max} {value}"
        
        # Cross-reference: slider knows its companion button
        s._companion = b
        
        # Bind slider value changes to update function
        s.bind(value=self.update_slider)
        
        # Flag to prevent sending OSC on initial drawing
        s._init = True
        
        # Initialize button text and message
        self.update_slider(s, value)
        
        # Create horizontal layout containing both widgets
        l = BoxLayout(orientation="horizontal")
        l.add_widget(b)
        l.add_widget(s)
        return l

    def update_slider(self, s, value):
        """
        Callback fired when slider value changes.
        Updates the companion button's text and sends OSC message.
        
        Args:
            s: The slider widget
            value: New slider value
        """
        # Round value for display
        s.value = round(value, 2)
        
        # Update button text to show current value
        s._companion.text = f"{s._param} {s.value}"
        s._companion._message = f"/param {s._param} {s.value}"        
        # Mark button as "clicked programmatically" to prevent config save
        s._companion._was_clicked = False
        
        # Send OSC message (except during initial UI build)
        if not s._init: 
            self.on_button(s._companion)
        
        # Clear init flag after first update
        s._init = False

    # ========================================================================
    # BUTTON EVENT HANDLERS
    # ========================================================================

    def on_button(self, button):
        """
        Handles button press events.
        Sends OSC message with "pressed" prefix.
        For parameter buttons, saves value to config if user-clicked.
        
        Args:
            button: The button widget that was pressed
        """
        now = time()
        
        # Debounce: ignore clicks within 0.2 seconds
        if getattr(button, "_last", 0) + 0.2 > now:
            return

        button._last = now
        
        # Generate unique node ID for this button press
        button._nodeID = int(time() * 100) % 10 ** 9
        
        # Check if this was a real user click vs programmatic trigger
        was_clicked = getattr(button, "_was_clicked", True)

        try:
            Logger.info(f"hi {button.text}")
            
            # Parse OSC message from button
            msg = button._message.split()
            address = msg.pop(0)  # e.g., "/note" or "/param"
            msg.insert(0, "pressed")  # Add event type
            
            # Send OSC message in background thread
            Thread(
                target=send_osc,
                args=(self.ip, self.port, address, msg),
                daemon=True,
            ).start()
            
            # Haptic feedback on mobile
            if can_vibrate: 
                vibrator.vibrate(0.075)
            
            # Check if this is a parameter button
            is_param = getattr(button, "_param", None)
            Logger.info(f"is_param {is_param}")
            
            # Save parameter value to config if user clicked (not programmatic)
            if is_param and was_clicked:
                self.rewrite_config([(is_param, msg[-1])])

        except Exception as e:
            Logger.error(f"button down: {e}")
            # Visual error feedback: red background
            button.background_normal = ""
            button.background_color = [1, 0, 0, 1]

        # Reset click flag for next time
        if not was_clicked:
            button._was_clicked = True

    def on_release_button(self, button):
        """
        Handles button release events.
        Sends OSC message with "release" prefix.
        
        Args:
            button: The button widget that was released
        """
        now = time()
        
        # Debounce: ignore releases within 0.2 seconds
        if getattr(button, "_uplast", 0) + 0.2 > now:
            return

        button._uplast = now
        
        try:
            Logger.info(f"hi up {button.text}")
            
            # Parse OSC message
            msg = button.text.split()
            address = msg.pop(0)
            msg.insert(0, "release")  # Add release event type
            
            # Send OSC message in background thread
            Thread(
                target=send_osc,
                args=(self.ip, self.port, address, msg),
                daemon=True,
            ).start()
            
        except Exception as e:
            Logger.error(f"button release {e}")
            # Visual error feedback
            button.background_normal = ""
            button.background_color = [1, 0, 0, 1]

    def send_all_params(self, button):
        for sld in self.all_param_sliders:
            self.on_button(sld._companion)

    def set_connect(self, button):
        """
        Handles the "Set" button press to update IP and port settings.
        Saves the new connection settings to config file.
        
        Args:
            button: The "Set" button widget
        """
        try:
            # Read values from text inputs
            self.ip = self.ip_text.text
            self.port = int(self.port_text.text)
            Logger.info(f"set {self.ip} {self.port}")
            
            # Save to config file
            self.rewrite_config()

        except Exception as e:
            Logger.error(e)
            # Visual error feedback for invalid input
            button.background_normal = ""
            button.background_color = [1, 0, 0, 1]


# ============================================================================
# APP ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    OSC().run()
