from .ZyTemp import ZyTemp, get_hiddev
from .mqtt import MqttClient
import time
import sys
import signal
import argparse
import logging as log


def signal_handler(signum, frame):
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='MQTT interface for Holtek USB-zyTemp CO2 sensors')
    parser.add_argument('--debug', action='store_true',
                        help='Debug log level')

    args = parser.parse_args()

    log.basicConfig(level=log.DEBUG if args.debug else log.INFO)

    signal.signal(signal.SIGINT, signal_handler)

    mqtt = MqttClient()
    mqtt.connect()

    try:
        while True:
            hiddev = get_hiddev()
            if not hiddev:
                time.sleep(5)
                continue
            zt = ZyTemp(hiddev, mqtt)
            zt.run()
            time.sleep(5)

    except SystemExit as e:
        mqtt.disconnect()
        log.log(log.INFO, 'Terminated')


if __name__ == '__main__':
    main()
