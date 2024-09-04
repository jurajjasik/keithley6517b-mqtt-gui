import json
import logging

import paho.mqtt.client as mqtt
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


# decorator to check if the client is connected
def client_connected(func):
    def wrapper(self, *args, **kwargs):
        if not self.client.is_connected():
            logger.warning("Client is not connected")
            return
        return func(self, *args, **kwargs)

    return wrapper


# decorator to log the function call
def log_func(func):
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        return func(*args, **kwargs)

    return wrapper


class Keithley6517B_MQTTClientLogic(QObject):
    signal_current = pyqtSignal(float)
    signal_state = pyqtSignal(object)
    device_status_changed = pyqtSignal(str)
    mqtt_status_changed = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()

        self.config = config
        self.topic_base = self.config["topic_base"]
        self.device_name = self.config["device_name"]

        self.client = mqtt.Client(
            clean_session=True,
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def start(self):
        self.client.connect(
            self.config["mqtt_broker"],
            self.config["mqtt_port"],
            self.config["mqtt_connection_timeout"],
        )
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        logger.debug(f"Connected with result code {rc}")

        self.client.subscribe(f"{self.topic_base}/response/{self.device_name}/#")
        self.client.subscribe(f"{self.topic_base}/connected/{self.device_name}")
        self.client.subscribe(f"{self.topic_base}/error/{self.device_name}")

        self.mqtt_status_changed.emit(
            f"connected to broker {self.config['mqtt_broker']}:{self.config['mqtt_port']}"
        )

    def on_message(self, client, userdata, message):
        topic = message.topic
        try:
            payload = json.loads(message.payload.decode())
        except json.JSONDecodeError as e:
            logger.debug(f"Error decoding message payload: {e}")
            payload = {}

        logger.debug(f"Received message on topic {topic} with payload {payload}")

        if "/connected/" in topic:
            self.handle_device_connected(message)
        elif "/error/" in topic:
            self.handle_device_error(message)
        elif topic.endswith("current"):
            self.handle_current(payload)
        elif topic.endswith("current_range"):
            self.handle_current_range(payload)
        elif topic.endswith("source_voltage"):
            self.handle_source_voltage(payload)
        elif topic.endswith("source_enable"):
            self.handle_source_voltage_enable(payload)
        elif topic.endswith("measure_continously"):
            self.handle_measure_continously(payload)

    def handle_device_connected(self, message):
        logger.info("Device connected")
        self.device_status_changed.emit("connected")

    def handle_device_error(self, message):
        logger.warning(f"Device error: {message.payload}")
        self.device_status_changed.emit("IO error")

    def handle_current(self, payload):
        if "value" in payload:
            try:
                current = float(payload["value"])
                self.signal_current.emit(current)
            except Exception as e:
                logger.warning(f"Error handling current message: {e}")

    def handle_current_range(self, payload):
        if "value" in payload:
            try:
                current_range = float(payload["value"])
                logger.debug(f"Current range: {current_range}")
                self.signal_state.emit({"current_range": current_range})
            except Exception as e:
                logger.warning(f"Error handling current range message: {e}")

    def handle_source_voltage(self, payload):
        if "value" in payload:
            try:
                voltage = float(payload["value"])
                logger.debug(f"Source voltage: {voltage}")
                self.signal_state.emit({"source_voltage": voltage})
            except Exception as e:
                logger.warning(f"Error handling source voltage message: {e}")

    def handle_source_voltage_enable(self, payload):
        if "value" in payload:
            try:
                enable = bool(payload["value"])
                logger.debug(f"Source voltage enable: {enable}")
                self.signal_state.emit({"source_voltage_enable": enable})
            except Exception as e:
                logger.warning(f"Error handling source voltage enable message: {e}")

    def handle_measure_continously(self, payload):
        if "value" in payload:
            try:
                state = bool(payload["value"])
                logger.debug(f"Measure continously: {state}")
                self.signal_state.emit({"measure_continously": state})
            except Exception as e:
                logger.warning(f"Error handling measure continously message: {e}")

    @client_connected
    @log_func
    def publish_source_voltage(self, voltage):
        self.client.publish(
            topic=f"{self.topic_base}/cmnd/{self.device_name}/source_voltage",
            payload=json.dumps({"value": voltage}),
        )


    @client_connected
    @log_func
    def publish_measure_continously(self, state):
        self.client.publish(
            topic=f"{self.topic_base}/cmnd/{self.device_name}/measure_continously",
            payload=json.dumps({"value": state}),
        )

    @client_connected
    @log_func
    def publish_source_voltage_enable(self, enable):
        self.client.publish(
            topic=f"{self.topic_base}/cmnd/{self.device_name}/source_enabled",
            payload=json.dumps({"value": enable}),
        )

    @client_connected
    @log_func
    def publish_shutdown(self):
        self.client.publish(
            topic=f"{self.topic_base}/cmnd/{self.device_name}/shutdown",
        )

    @client_connected
    @log_func
    def publish_reset(self):
        self.client.publish(
            topic=f"{self.topic_base}/cmnd/{self.device_name}/reset",
        )

    @client_connected
    @log_func
    def publish_measure(self, nplc, current, auto_range):
        self.client.publish(
            topic=f"{self.topic_base}/cmnd/{self.device_name}/measure_current",
            payload=json.dumps(
                {
                    "nplc": nplc,
                    "current": current,
                    "auto_range": auto_range,
                }
            ),
        )

    @client_connected
    @log_func
    def publish_current_range(self, value):
        self.client.publish(
            topic=f"{self.topic_base}/cmnd/{self.device_name}/current_range",
            payload=json.dumps({"value": value}),
        )
