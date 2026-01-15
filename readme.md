# pyapp-osc

this is an app to show buttons and use them to send
messages to an OSC server (e.g. supercollider)

on a computer a file is created or read in ./Documents/osc_config.ini

on an android phone this is in shared phblic Documents folder.

the file is a list of messages (or blank lines to skip) which will be
sent to OSC server and written on the buttons

the (current subject to change) layout is two big buttons and a 4x4 grid of 16 button spaces. the main buttons are always
drawn, if any of the 16 are blank a button is replaced with empty space.

if android app is replaced or updated the previous osc_config.ini file
should be removed or renamed first, trying to read a previous one will result in a crash. new versions of the app should be left to write their own and the result overwritten by previous

