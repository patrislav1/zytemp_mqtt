
#!/usr/bin/env python3
"""
SPDX-License-Identifier: BSD-3-Clause
This file is part of zytemp-mqtt, https://github.com/patrislav1/zytemp_mqtt
Copyright (C) 2022 Patrick Huesmann <info@patrick-huesmann.de>
"""

import setuptools
from pathlib import Path as path
from zytempmqtt import __version__

readme_contents = path('./README.md').read_text()
requirements = path('./requirements.txt').read_text().splitlines()
packages = setuptools.find_packages(include=['zytempmqtt'])

setuptools.setup(
    name='zytemp_mqtt',
    version=__version__,
    author='Patrick Huesmann',
    author_email='info@patrick-huesmann.de',
    url='https://github.com/patrislav1/zytemp_mqtt',
    license='BSD',
    description='MQTT interface for Holtek USB-zyTemp CO2 sensors',
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    keywords='zytemp holtek mqtt co2sensor homeassistant',
    install_requires=requirements,
    packages=packages,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Operating System :: Linux',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
    ],
    entry_points={
        'console_scripts': [
            'zytempmqtt=zytempmqtt.cli:main',
        ],
    },
    python_requires='>=3.6'
)
