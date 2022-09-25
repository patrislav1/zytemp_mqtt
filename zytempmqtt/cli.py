from .ZyTemp import get_dev
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
            zt = get_dev()
            if not zt:
                time.sleep(5)
                continue
            zt.run(mqtt)
            time.sleep(5)

    except SystemExit as e:
        log.log(log.INFO, 'Terminated')


if __name__ == '__main__':
    main()
