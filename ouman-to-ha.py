#!env python3
# -*- coding: utf-8 -*-

# Software to read data from Ouman EH203 and save those to Home Assistant

import argparse
import os.path
import sys

import ConfigParser
import paho.mqtt.client as mqtt

# add taloLogger directory to module path
sys.path = [os.path.abspath('taloLogger')] + sys.path

from modules.core import configuration, log
from modules.datasources.ouman import oumanSerial

topic_base = "home/eh203/"
values_to_publish = [
    "ulkolampotila",
    "l1_menovesi",
    "l1_paluuvesi",
    "l2_menovesi"
]

g_logger = None
g_publish_config = None


class MqttConfig:
    def __init__(self, username, password, host, port):
        self.username = username
        self.password = password
        self.host = host
        self.port = port

    def __repr__(self):
        return "username={}, host={}, port={}".format(self.username,
                                                      self.host,
                                                      self.port)


class PublishConfig:
    def __init__(self, topic, values):
        self.topic = topic
        self.values = self.parse_values(values)

    def parse_values(self, values):
        tmp = []
        for value in values.split(","):
            value = value.strip().lower()
            value = value.replace(" ", "_")
            tmp.append(value)
        return tmp

    def __repr__(self):
        return "topic={}, values={}".format(self.topic,
                                            self.values)


def parse_ini_config(logger):
    config = ConfigParser.ConfigParser()
    config.read('ouman-collector.ini')

    error_in_ini = False

    # mqtt section validation
    if "mqtt" not in config.sections():
        logger.log("ini configuration is missing mqtt section")
        error_in_ini = True

    needed = ["username", "password", "host", "port"]
    keys = [x[0] for x in config.items("mqtt")]
    for key in needed:
        if key not in keys:
            logger.log("ini configuration is missing mqtt/{} key". format(key))
            error_in_ini = True

    # publish section validation
    if "publish" not in config.sections():
        logger.log("ini configuration is missing mqtt section")
        error_in_ini = True

    needed = ["topic", "values"]
    keys = [x[0] for x in config.items("publish")]
    for key in needed:
        if key not in keys:
            logger.log("ini configuration is missing publish/{} key".format(key))
            error_in_ini = True

    if error_in_ini:
        sys.exit(1)

    # Everything is valid, so let's create configurations
    mqtt_config = MqttConfig(
        config.get("mqtt", "username"),
        config.get("mqtt", "password"),
        config.get("mqtt", "host"),
        config.get("mqtt", "port")
    )

    publish_config = PublishConfig(
        config.get("publish", "topic"),
        config.get("publish", "values")
    )
    global g_publish_config
    g_publish_config = publish_config

    return mqtt_config


def parse_args():
    help_text = "Read data from Ouman device and publish to Home assistant"
    parser = argparse.ArgumentParser(description=help_text)
    parser.add_argument('--serial',
                        type=str,
                        required=True,
                        help="Serial device to use, example=/dev/ttyUSB0")
    parser.add_argument('--ouman',
                        type=str,
                        required=True,
                        help="Ouman device to use, example=EH203")
    parser.add_argument('--debug',
                        action='store_true',
                        default=False,
                        help='Activate debug logging')
    return parser.parse_args()


def on_connect(client, userdata, flags, rc):

    if rc != 0:
        g_logger.log("MQTT connection result code: {}".format(rc))

    for key in g_publish_config.values:
        value = userdata[key]
        final_topic = g_publish_config.topic + key + "/value"

        g_logger.log("Publish values to {}, value={}".format(final_topic, value))
        client.publish(topic=final_topic, payload=value, qos=0, retain=False)


def _initialize_logging(debug):
    conf = configuration.Configuration()
    conf.addConfigurable(log.Logger)
    conf.setValue('CONSOLE_LOGGING', 'true')
    if debug:
        conf.setValue('VERBOSE_LOGGING', 'true')
    logger = log.Logger(conf)
    log.Logging.setLogger(logger)

    # Hack to use logger in on_connect
    global g_logger
    g_logger = logger
    return logger


def _read_ouman_data(args, logger):
    ouman_serial = oumanSerial.OumanSerial(args.serial, args.ouman)
    measurements = {}
    for key in oumanSerial.OUMAN_DEVICES[args.ouman]:
        data = ouman_serial.runQueryCommand(key[0])
        if len(data) > 0:
            logger.log("From device " + key[0] + ': ' + data)

            try:
                data = int(data)
            except ValueError:
                try:
                    data = float(data)
                except ValueError:
                    pass

            # Replace incoming value to better suitable one
            key = key[0]
            key = key.replace(' ', '_')
            key = key.replace('-', '_')
            key = key.lower()

            measurements[key] = data
        else:
            logger.log(key[0] + ': ERROR')

    return measurements


def publish_measurements(mqtt_conf, measurements):
    client = mqtt.Client(userdata=measurements)
    client.username_pw_set(mqtt_conf.username, mqtt_conf.password)
    client.on_connect = on_connect
    client.connect(mqtt_conf.host, mqtt_conf.port)
    client.loop_start()
    client.loop_write()
    client.loop_stop()


def main():
    args = parse_args()

    logger = _initialize_logging(args.debug)
    mqtt_conf = parse_ini_config(logger)

    if args.ouman not in oumanSerial.OUMAN_DEVICES:
        logger.log("Given ouman device not found from taloLogger library")
        logger.log("Valid devices are: {}".format(oumanSerial.OUMAN_DEVICES.keys()))
        sys.exit(1)

    if not os.path.exists(args.serial):
        logger.log("Given serial device: {} not found".format(args.serial))
        sys.exit(1)

    logger.log("Starting to read data from OUMAN device")

    measurements = _read_ouman_data(args, logger)

    publish_measurements(mqtt_conf, measurements)


if __name__ == "__main__":
    main()
