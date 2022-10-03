from time import time
import logging as log
from .config import ConfigFile

import paho.mqtt.client as mqtt

class MqttClient:
    def __init__(self):
        self.cfg = ConfigFile()
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        self.connected = (rc == 0)
        if rc == 0:
            log.log(log.INFO, f'MQTT connected')
        else:
            log.log(log.ERROR, f'MQTT connection failed: {rc}')

    def on_disconnect(self, client, userdata, rc):
        self.connected = False

    def connect(self):
        self.disconnected = (False, None)
        self.t = time()

        self.client = mqtt.Client(client_id=self.cfg.mqtt_client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(
            self.cfg.mqtt_username, self.cfg.mqtt_password)
        self.client.connect(
            self.cfg.mqtt_host, self.cfg.mqtt_port)

    def publish(self, topic, pkt):
        self.client.publish(self.cfg.mqtt_topic_root + '/' + topic, pkt)

    def run(self, to):
        self.client.loop(timeout=to)
