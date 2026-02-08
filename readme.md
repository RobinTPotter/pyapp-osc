# pyapp-osc

this is an app to show buttons and use them to send
messages to an OSC server (e.g. supercollider)

there is _no feedback_ from the server.

buttons and slider controls are named in a file `osc_config.ini` which is stored internally for android and desktop apps.

the host and port to send the messages to are also stored here. this config can be exported or imported using the _E_ and _I_ buttons in the top row of the app, the host and port are set here too.

the _Sn_ button sends all the values of params in one go and saves to config, this is to ensure the current slider value is sent.


the config file is the list of messages (or blank lines to skip and not create a button) which will be sent to OSC server and written on the buttons.

a line is of the form: `/address [arg1 arg2..]`. the OSC message will be address and the remaining args as a list.

it should be assumed by the OSC server that the args are strings and likely need casting as appropriate.

the (current subject to change) layout is 4x2 big buttons and a 5x4 grid of 20 button spaces. if any of the first 28 config lines are blank a button is replaced with empty space.

swipe the top grid to reveal paramters. slider values are sent in real time, slider values are written back to the config
when the corresponding button is pressed. parameters are read/written to config in the form:

`/param name min max value`

param message has a special meaning, all other lines add a button in top or bottom grid. a param creates a button and slider pair with the lower and upper bound and initial value. the button text is updated by the slider, the message is also sent (attempted at least).

adding a #/param line will make a carousel split such that subsequent parameters will appear on the next screen.

sample config:

```
192.168.1.174
57120
/voice/sine

/voice/saw

/voice/pulse


/voice/vox
/note 60
/note 61


/note 75
/note 76
/record
/stopRecord
/freeAll
/param a1 0.0 1.0 0.0
/param a2 0.0 1.0 0.5
#/param
/param a3 0.0 1.0 0.0
/param a4 0.0 1.0 0.8
```

when a button is pressed the messages are send to the host and port. for normal buttons the defined message in config is sent to the address. in the case of a slider, the message is the name of the parameter and the current value. for all messages "pressed" or "released" is inserted at the start of the message. this is so the listener has the option to react accordingly.



---

note on building. there is a GitHub workflow and buildozer.spec. also a buildozer.spec.local for when nobody is using Minecraft. this uses a BUILD_NO env var to set the version as 0.1.XXX


cd pyapp-osc
podman run -it --rm -v 



%cd%\.buildozer:/home/user/.buildozer -v %cd%:/home/user/hostcwd -e BUILD_NO=43 kivy/buildozer -s buildozer.spec.local android debug







