# Get Iplayer Interface

This is a simple command line interface to work with the [get_iplayer](https://github.com/get-iplayer/get_iplayer) application. 

It gives the user the ability to do a keyword search or list available episodes by channel. 

It then passes the pid's for the chosen downloads to a docker container that incorporates a VPN to England to do the actual downloads.


## Requirements
needs a config.py with location and name of log file
LOG_LOCATION=''
