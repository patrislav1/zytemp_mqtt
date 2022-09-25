from .ZyTemp import get_dev
import time
import sys

import signal


def signal_handler(signum, frame):
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    try:
        while True:
            zt = get_dev()
            if not zt:
                time.sleep(5)
                continue
            zt.run()
            time.sleep(5)

    except SystemExit as e:
        print('Terminated')


if __name__ == '__main__':
    main()
