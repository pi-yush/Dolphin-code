import subprocess
import sys
import dbus, time
from time import sleep
import signal, os

BT_ADDR = "<Bluetooth's MAC address>"

def enable_modem():
    bus = dbus.SystemBus()
    try:
        manager = dbus.Interface(bus.get_object('org.ofono', '/'),'org.ofono.Manager')
    except dbus.exceptions.DBusException as e:
        print ("Can't access org.ofono on DBus: {}".format(e))
        exit(1)
    modems = manager.GetModems()
    path = modems[0][0]
    print("Connecting modem %s..." % path)
    modem = dbus.Interface(bus.get_object('org.ofono', path),'org.ofono.Modem')
    try:
        modem.SetProperty("Powered", dbus.Boolean(1), timeout = 120)
    except dbus.exceptions.DBusException as e:
        print("Can't set modem 'Powered': {}".format(e))
        exit(1)

def restart_bluetooth():
	os.system("pulseaudio -k")
	os.system("sudo systemctl restart bluetooth")
	sleep(1)
	os.system("bluetoothctl -- pairable on")
	sleep(1)
	os.system(f"bluetoothctl -- info {BT_ADDR}")
	os.system(f"bluetoothctl -- pair {BT_ADDR}")
	os.system(f"bluetoothctl -- connect {BT_ADDR}")
	sleep(1)
