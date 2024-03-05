# Ouman EH203 data collector for Home assistant

Uses taloLogger to interface with Ouman EH203 over serial cable.
Send result to MQTT to store and visualize data in Home assistant.

### What's needed

 * Ouman EH203 connected via serial cable to (a device such as Raspberry Pi)
    * Check connection instructions from http://ouman.fi/documentbank/EH-203__manual__fi.pdf -> page 42.
 * Home assistant with mqtt server installed

### SW requirements

 * taloLogger https://olammi.iki.fi/sw/taloLogger/ (tested with v1.7k)
 * Python 2.7.x
 * Install requirements for python2


## Download and extract taloLogger

[Download taloLogger](https://olammi.iki.fi/sw/taloLogger/download.php) to this same directory and extract the contents to `taloLogger/` directory.

Modify `ouman-to-ha.ini` file to match to your needs.

You need to check available publish/values options from taloLogger/modules/datasources/ouman/oumanSerial.py based on your device/needs


## Run

I was having problem to use this without sudo permissions.
It seems that opening tty device was needing those, but you can try without.

Run the collector with example:

```
sudo python2 ouman-to-ha.py --serial /dev/ttyUSB0 --ouman EH203
```

Available flags:
```sh
python2 ouman-to-ha.py -h
usage: ouman-to-ha.py [-h] --serial SERIAL --ouman OUMAN [--debug]

Read data from Ouman device and publish to Home assistant

optional arguments:
  -h, --help       show this help message and exit
  --serial SERIAL  Serial device to use, example=/dev/ttyUSB0
  --ouman OUMAN    Ouman device to use, example=EH203
  --debug          Activate debug logging
```


Crontab example, replace USERNAME with your username/path.

```
* * * * * cd /home/USERNAME/ouman-to-ha/taloLogger/ ; sudo python2 ouman-to-ha.py /dev/ttyUSB0 EH203
```

# Configuration to Home assistant
I am not fully sure, is it possible to setup this in UI, so this only show how to do it in yaml files.

1. Add row `mqtt: !include mqtt_sensors.yaml` to `configuration.yaml`
2. Add this configuration inside of `configuration.yaml`, of course adapt based on your needs!
   
   `state_topic` values are generated from given topic and values given.
   
   value is lowercase, whitespace replaced with _, so example L1 Menovesi is l1_menovesi


```sh
- sensor:
    name: "EH203 Ulkolämpötila"
    unique_id: eh203_ulkolampotila
    state_topic: "home/eh203/ulkolampotila/value"
    device_class: temperature
    unit_of_measurement: "°C"
    state_class: measurement

- sensor:
    name: "EH203 L1 menovesi"
    unique_id: eh203_l1_menovesi
    state_topic: "home/eh203/l1_menovesi/value"
    device_class: temperature
    unit_of_measurement: "°C"
    state_class: measurement

- sensor:
    name: "EH203 L1 paluuvesi"
    unique_id: eh203_l1_paluuvesi
    state_topic: "home/eh203/l1_paluuvesi/value"
    device_class: temperature
    unit_of_measurement: "°C"
    state_class: measurement

- sensor:
    name: "EH203 L2 menovesi"
    unique_id: eh203_l2_menovesi
    state_topic: "home/eh203/l2_menovesi/value"
    device_class: temperature
    unit_of_measurement: "°C"
    state_class: measurement
```

restart home assistant service to see 