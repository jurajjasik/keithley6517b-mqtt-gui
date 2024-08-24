import logging

import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from PyQt5.QtCore import QObject

logger = logging.getLogger(__name__)


class Keithley6517B_MQTTClientLogic(QObject):
    def __init__(self, config):
        super().__init__()

        self.config = config
        self.topic_base = self.config["topic_base"]
        self.device_name = self.config["device_name"]

        self.client = mqtt.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            clean_session=True,
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.start()

    def start(self):
        self.client.connect(
            self.config["mqtt_broker"],
            self.config["mqtt_port"],
            self.config["mqtt_connection_timeout"],
        )
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, properties):
        logger.debug(f"Connected with result code {rc}")

        self.client.subscribe(f"{self.topic_base}/response/{self.device_name}/#")

        self.client.subscribe(f"{self.topic_base}/connected/{self.device_name}")

        self.client.subscribe(f"{self.topic_base}/connected/{self.device_name}")

    def on_message(self, client, userdata, message):
        print(
            f"Received message '{message.payload.decode()}' on topic '{message.topic}'"
        )
