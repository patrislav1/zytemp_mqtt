# https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor

import hid
from hid import device

CO2_USB_MFG = 'Holtek'
CO2_USB_PRD = 'USB-zyTemp'

hid_sensors = [
    e for e in hid.enumerate()
    if e['manufacturer_string'] == CO2_USB_MFG
    and e['product_string'] == CO2_USB_PRD
]

for s in hid_sensors:
    intf, path, vid, pid = (s[k] for k in (
        'interface_number', 'path', 'vendor_id', 'product_id'))
    path_str = path.decode('utf-8')
    print(
        f'Found CO2 sensor at intf. {intf}, {path_str}, VID={vid:04x}, PID={pid:04x}')

h = device()
h.open_path(path)

h.send_feature_report(bytearray(
    [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]))

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

while True:
    r = h.read(8)
    if not r:
        print("Read error")
        continue

    if r[4] != 0x0d:
        print("Unexpected data from device")
        continue

    if r[3] != sum(r[0:3]) & 0xff:
        print("Checksum error")
        continue

    m_type = r[0]
    m_val = r[1] << 8 | r[2]

    try:
        m = MEASUREMENTS[m_type]
    except KeyError:
        #        print(f'Unknown key {m_type:02x}')
        continue

    m_name, m_unit, m_reading = m['name'], m['unit'], m['conversion'](m_val)

    print(f'{m_name}: {m_reading:g} {m_unit}')
