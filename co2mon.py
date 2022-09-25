# https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor

import hid
import sys
import time

CO2_USB_MFG = 'Holtek'
CO2_USB_PRD = 'USB-zyTemp'

# Ignore first 5 measurements during self-calibration after power-up
IGNORE_N_MEASUREMENTS = 5


class ZyTemp():
    MEASUREMENTS = {
        0x42: {
            'name': 'Temperature',
            'unit': '°C',
            'conversion': lambda x: x / 16 - 273.15,
        },
        0x50: {
            'name': 'CO2',
            'unit': 'ppm',
            'conversion': lambda x: x,
        },
    }

    def __init__(self, hiddev):
        self.h = hiddev
        self.h.send_feature_report(b'\xc4\xc6\xc0\x92\x40\x23\xdc\x96')
        self.measurements_to_ignore = IGNORE_N_MEASUREMENTS

    def run(self):
        while True:
            try:
                r = self.h.read(8)
            except OSError as err:
                print(f'OS error: {err}')
                return

            if not r:
                print(f'Read error')
                self.h.close()
                return

            if r[4] != 0x0d:
                print(f'Unexpected data from device')
                continue

            if r[3] != sum(r[0:3]) & 0xff:
                print(f'Checksum error')
                continue

            m_type = r[0]
            m_val = r[1] << 8 | r[2]

            try:
                m = ZyTemp.MEASUREMENTS[m_type]
            except KeyError:
                #        print(f'Unknown key {m_type:02x}')
                continue

            m_name, m_unit, m_reading = m['name'], m['unit'], m['conversion'](
                m_val)

            ignore = self.measurements_to_ignore > 0

            print(f'{m_name}: {m_reading:g} {m_unit}' +
                  (' (ignored)' if ignore else ''))

            if m_name == 'CO2' and self.measurements_to_ignore:
                self.measurements_to_ignore -= 1


def get_dev():
    hid_sensors = [
        e for e in hid.enumerate()
        if e['manufacturer_string'] == CO2_USB_MFG
        and e['product_string'] == CO2_USB_PRD
    ]

    p = []
    for s in hid_sensors:
        intf, path, vid, pid = (
            s[k] for k in
            ('interface_number', 'path', 'vendor_id', 'product_id')
        )
        path_str = path.decode('utf-8')
        print(
            f'Found CO2 sensor at intf. {intf}, {path_str}, VID={vid:04x}, PID={pid:04x}')
        p.append(path)

    if not p:
        print('No device found', file=sys.stderr)
        return None

    print(f'Using device at {p[0].decode("utf-8")}')
    h = hid.device()
    h.open_path(path)

    return ZyTemp(h)


if __name__ == '__main__':
    while True:
        zt = get_dev()
        if not zt:
            time.sleep(5)
            continue
        zt.run()
        time.sleep(5)
