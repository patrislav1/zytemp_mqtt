import yaml
import os
import logging as log

APPLICATION_NAME = 'zytemp-mqtt'


class ConfigFile(object):
    CONFIG_DEFAULTS = {
        'mqtt_host': None,
        'mqtt_port': 1883,
        'mqtt_username': None,
        'mqtt_password': None,
        'mqtt_client_id': APPLICATION_NAME,
        'mqtt_topic': APPLICATION_NAME,
        'friendly_name': APPLICATION_NAME,
        'discovery_prefix': 'homeassistant',
    }

    _instance = None

    def _initialize(self):
        self.cfg_dir = os.path.join(
            os.path.expanduser('~'), '.config', APPLICATION_NAME
        )
        self.cfg_file_path = os.path.join(self.cfg_dir, 'config.yaml')
        if not os.path.isfile(self.cfg_file_path):
            self.cfg_file_path = '/etc/zytempmqtt/config.yaml'

        try:
            with open(self.cfg_file_path, 'r') as infile:
                cfg_dict = yaml.safe_load(infile)
            for k, v in ConfigFile.CONFIG_DEFAULTS.items():
                setattr(self, k,
                        cfg_dict[k] if k in cfg_dict else v)

        except OSError as e:
            log.log(log.WARN, e)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigFile, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
