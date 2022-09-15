# Dolphin
All of the dolphin experiments were performed on platform with given details:

Ofono version : 1.31 (ofonod --version)  
BlueZ version : 5.53-0ubuntu3 (dpkg --status bluez | grep '^Version:')  
PulseAudio version : pulseaudio 13.99.1 (pulseaudio --version)  
Alsa version : Advanced Linux Sound Architecture Driver Version k5.4.0-40-generic (cat /proc/asound/version)  

Bluetooth enabled Ubuntu 20.04 LTS  
Sound card : HDA-Intel - HDA Intel PCH (cat /proc/asound/cards)  
Kernel version : 5.4.0-40-generic (uname -r)  

Dolphin uses the ofono telephony framework for Linux which can be installed using : `apt-get install ofono`

After installing ofono, navigate to file "/etc/pulse/default.pa". In this file, find the line "load-module module-bluetooth-discover".  
Change it to "load-module module-bluetooth-discover headset=ofono".  

If user "pulse" is not a member of group "bluetooth", then add it: "useradd -g bluetooth pulse".

For the sake of simplicity, let's define some keywords.  
1. Server or client "side" - Here, side will refer to the pair of bluetooth enabled smartphone and bluetooth enabled linux machine.

For all the applications given in the directories, the following information will be required by the user to supply manually:  
1. Server side smartphone and client side smartphone phone number (IMSI number)  
2. Smartphone bluetooth's MAC address - For this, connect linux machine and smartphone with bluetooth (using GUI) and then list MAC addresses of connected devices on linux machine using : bluetoothctl -- paired-devices  
3. Names of pulseaudio source and sinks due to bluetooth connection - For this, manually place and connect a call from the side's smartphone (bluetooth connected with linux host). After this, run ``pactl list sources short | cut -f 2 | grep bluez_source`` to get the name of pulseaudio source and run ``pactl list sinks short | cut -f 2 | grep bluez_sink`` to get the name of pulseaudio sink.  

The rest of directories can be explored only after all this configuration is done.
