import logging as log
import paho.mqtt.client as mqtt
import json

from .config import ConfigFile

l = log.getLogger('mqtt')


class MqttClient:
    def __init__(self):
        self.cfg = ConfigFile()
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        self.connected = (rc == 0)
        if rc == 0:
            l.log(log.INFO, f'connected to {self.cfg.mqtt_host}')
        else:
            l.log(log.ERROR,
                  f'connection to {self.cfg.mqtt_host} failed: {rc}')

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        l.log(log.WARN, f'disconnected from {self.cfg.mqtt_host}: {rc}')

    def connect(self):
        self.client = mqtt.Client(client_id=self.cfg.mqtt_client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(
            self.cfg.mqtt_username, self.cfg.mqtt_password)
        try:
            self.client.connect(
                self.cfg.mqtt_host, self.cfg.mqtt_port)
        except Exception as e:
            l.log(log.ERROR, f'connection to {self.cfg.mqtt_host} failed: {e}')

    def disconnect(self):
        if self.connected:
            self.client.disconnect()

    def publish(self, topic, pkt, retain=False):
        def round_floats(o):
            if isinstance(o, float):
                return round(o, 5)
            if isinstance(o, dict):
                return {k: round_floats(v) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                return [round_floats(x) for x in o]
            return o
        if self.connected:
            self.client.publish(topic, json.dumps(
                round_floats(pkt)), retain=retain)

    def run(self, to):
        if not self.connected:
            self.connect()

        self.client.loop(timeout=to)
