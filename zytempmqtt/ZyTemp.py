# https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor

import hid
import os
import sys
import time
import logging as log
from .config import ConfigFile

CO2_USB_MFG = 'Holtek'
CO2_USB_PRD = 'USB-zyTemp'

# Ignore first 5 measurements during self-calibration after power-up
IGNORE_N_MEASUREMENTS = 5

l = log.getLogger('zytemp')


_CO2MON_MAGIC_WORD = b'Htemp99e'
_CO2MON_MAGIC_TABLE = (0, 0, 0, 0, 0, 0, 0, 0)

def list_to_longint(x):
    return sum([val << (i * 8) for i, val in enumerate(x[::-1])])

def longint_to_list(x):
    return [(x >> i) & 0xFF for i in (56, 48, 40, 32, 24, 16, 8, 0)]


class ZyTemp():
    MEASUREMENTS = {
        0x42: {
            'name': 'Temperature',
            'unit': '°C',
            'conversion': lambda x: x / 16 - 273.15,
            'ha_device_class': 'temperature',
            'ha_icon': 'mdi:thermometer',
        },
        0x50: {
            'name': 'CO2',
            'unit': 'ppm',
            'conversion': lambda x: x,
            'ha_device_class': 'carbon_dioxide',
            'ha_icon': 'mdi:molecule-co2',
        },
    }

    def __init__(self, hiddev, mqtt):
        self.cfg = ConfigFile()
        self.m = mqtt
        self.h = hiddev
        self.measurements_to_ignore = IGNORE_N_MEASUREMENTS
        self.values = {v['name']: None for v in ZyTemp.MEASUREMENTS.values()}

        self._magic_word = [((w << 4) & 0xFF) | (w >> 4)
                            for w in bytearray(_CO2MON_MAGIC_WORD)]
        self._magic_table = _CO2MON_MAGIC_TABLE
        self._magic_table_int = list_to_longint(_CO2MON_MAGIC_TABLE)

        self.h.send_feature_report(self._magic_table)

    def __del__(self):
        self.h.close()

    """ MQTT Discovery for Home Assistant """

    def discovery(self):
        if not len(self.cfg.discovery_prefix):
            return

        for meas in ZyTemp.MEASUREMENTS.values():
            id = os.path.basename(self.cfg.mqtt_topic)
            config_content = {
                'device': {
                    'identifiers': [id],
                    'manufacturer': CO2_USB_MFG,
                    'model': CO2_USB_PRD,
                    'name': self.cfg.friendly_name,
                },
                'enabled_by_default': True,
                'state_class': 'measurement',
                'device_class': meas['ha_device_class'],
                'name': ' '.join((self.cfg.friendly_name, meas['name'])),
                'state_topic': self.cfg.mqtt_topic,
                'unique_id': '_'.join((id, meas['name'])),
                'unit_of_measurement': meas['unit'],
                'value_template': '{{ value_json.%s }}' % meas['name'],
                'icon': meas['ha_icon']
            }
            self.m.publish(
                os.path.join(
                    self.cfg.discovery_prefix, 'sensor', config_content['unique_id'], 'config'
                ),
                config_content,
                retain=True
            )

        self.m.run(0.1)

    def update(self, key, value):
        if self.values[key] == value:
            return

        self.values[key] = value

        if any(v is None for v in self.values.values()):
            return

        self.m.publish(self.cfg.mqtt_topic, self.values)

    def run(self):
        self.discovery()
        while True:
            try:
                r = self.h.read(8)
            except OSError as err:
                l.log(log.ERROR, f'OS error: {err}')
                return

            if not r:
                l.log(log.ERROR, f'Read error')
                self.h.close()
                return

            # Rearrange message and convert to long int
            msg = list_to_longint([r[i] for i in [2, 4, 0, 7, 1, 6, 5, 3]])
            # XOR with magic_table
            res = msg ^ self._magic_table_int
            # Cyclic shift by 3 to the right
            res = (res >> 3) | ((res << 61) & 0xFFFFFFFFFFFFFFFF)
            # Convert to list
            res = longint_to_list(res)
            # Subtract and convert to uint8
            r = [(r - mw) & 0xFF for r, mw in zip(res, self._magic_word)]

            if r[4] != 0x0d:
                l.log(log.DEBUG, f'Unexpected data from device')
                continue

            if r[3] != sum(r[0:3]) & 0xff:
                l.log(log.ERROR, f'Checksum error')
                continue

            m_type = r[0]
            m_val = r[1] << 8 | r[2]

            try:
                m = ZyTemp.MEASUREMENTS[m_type]
            except KeyError:
                l.log(log.DEBUG, f'Unknown key {m_type:02x}')
                continue

            m_name, m_unit, m_reading = m['name'], m['unit'], m['conversion'](
                m_val)

            ignore = self.measurements_to_ignore > 0

            l.log(log.DEBUG, f'{m_name}: {m_reading:g} {m_unit}' +
                  (' (ignored)' if ignore else ''))

            if not ignore:
                self.update(m_name, m_reading)
            self.m.run(0.1)

            if m_name == 'CO2' and self.measurements_to_ignore:
                self.measurements_to_ignore -= 1


def get_hiddev():
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
        l.log(log.INFO,
              f'Found CO2 sensor at intf. {intf}, {path_str}, VID={vid:04x}, PID={pid:04x}')
        p.append(path)

    if not p:
        l.log(log.ERROR, 'No device found')
        return None

    l.log(log.INFO, f'Using device at {p[0].decode("utf-8")}')
    h = hid.device()
    h.open_path(p[0])
    return h
