# pyapp-osc

this is an app to show buttons and use them to send
messages to an OSC server (e.g. supercollider)

on a computer a file is created or read in ./Documents/osc_config.ini

on an android phone this is in shared public Documents folder.

the file is the list of messages (or blank lines to skip and not create a button depending on
the set of buttons used) which will be sent to OSC server and written on the buttons. a
line is of the form: `address [arg1 arg2..]`. the OSC message will be address and the remaining args as a list.

it should be assumed by the OSC server that the args are strings

the (current subject to change) layout is 2x2 big buttons and a 4x4 grid of 16 button spaces. the main buttons are always
drawn, if any of the 16 are blank a button is replaced with empty space.

if android app is replaced or updated the previous osc_config.ini file
should be removed or renamed first, trying to read a previous one will result in a crash. new versions of the app should be left to write their own and the result overwritten by previous

swipe the top grid to reveal paramters, sliders are sent in real time, slider values are written back to the config
when the corresponding button is pressed. parameters are read/written to config in the form:

`/param name min max value`

param message has a special meaning, all other lines add a button in top or bottom grid

adding a #/param line will make a carousel split such that subsequent parameters will appear on the next screen.

---

note on building. there is a GitHub workflow and buildozer.spec. also a buildozer.spec.local for when nobody is using Minecraft. this uses a BUILD_NO env var to set the version as 0.1.XXX


cd pyapp-osc
podman run -it --rm -v %cd%\.buildozer:/home/user/.buildozer -v %cd%:/home/user/hostcwd -e BUILD_NO=43 kivy/buildozer android debug

