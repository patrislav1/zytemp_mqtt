import uuid
from time import time
import logging as log

import paho.mqtt.client as mqtt


class MqttClient:
    def __init__(self):
        self.client_id = 'zytemp_mqtt/' + str(uuid.uuid4())
        self.topic_root = self.client_id
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

        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.connect('homeassistant.fritz.box', 1883)

    def publish(self, topic, pkt):
        self.client.publish(self.topic_root + '/' + topic, pkt)

    def run(self, to):
        self.client.loop(timeout=to)
