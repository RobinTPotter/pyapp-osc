[app]
title = OSC
package.name = osc
package.domain = org.robins
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,plyer
orientation = portrait
osx.kivy_version = 2.1.0
android.permissions = INTERNET,VIBRATE
android.adaptive_icon.foreground = icon_foreground.png
android.adaptive_icon.background = icon_background.png
presplash.filename = presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
