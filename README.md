# esp8266-gdl90
Scripts to receive GDL90 packets using esp8266 AT commands

This is not a full featured receiver and parser. After finding no examples about
how to connect and receive UDP packets I wrote this to work through how to receive
GDL90 coming from a stratux device on port 4000. This is not robust and succeeds
based on winning a race 90% of the time when the esp8266 starts up.
