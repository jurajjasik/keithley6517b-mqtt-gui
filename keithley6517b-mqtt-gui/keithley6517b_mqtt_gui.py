import paho.mqtt.client as mqtt

from PyQt5.QtWidgets import QMainWindow, QGridLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox, QGroupBox, QFormLayout, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup, QSlider, QLCDNumber, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

import time
import os
import json
import logging

class Keithley6517B_MQTT_GUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Keithley 6517B MQTT GUI")
        self.setWindowIcon(QIcon("icon.png"))

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()

        self.init_ui()

    def init_ui(self):
        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        self.init_controls()
        self.init_layout()

        self.setLayout(self.grid)

    def init_controls(self):
        self.voltage_label = QLabel("Voltage (V)")
        self.voltage_input = QDoubleSpinBox()
        self.voltage_input.setRange(-2100.0, 2100.0)
        self.voltage_input.setSingleStep(0.1)
        self.voltage_input.setValue(0.0)

        self.current_label = QLabel("Current (A)")
        self.current_input = QDoubleSpinBox()
        self.current_input.setRange(-2.0e-12, 2.0e-12)
        self.current_input.setSingleStep(1.0e-13)
        self.current_input.setValue(0.0)

        self.resistance_label = QLabel("Resistance (Ohm)")
        self.resistance_input = QDoubleSpinBox()
        self.resistance_input.setRange(0.0, 2.0e12)
        self.resistance_input.setSingleStep(1.0e6)
        self.resistance_input.setValue(0.0)

        self.measure_button = QPushButton("Measure")
        self.measure_button.clicked.connect(self.measure)

    def init_layout(self):
        self.grid.addWidget(self.voltage_label, 0, 0)
        self.grid.addWidget(self.voltage_input, 0, 1)

        self.grid.addWidget(self.current_label, 1, 0)
        self.grid.addWidget(self.current_input, 1, 1)

        self.grid.addWidget(self.resistance_label, 2, 0)
        self.grid.addWidget(self.resistance_input, 2, 1)

        self.grid.addWidget(self.measure_button, 3, 0, 1, 2)

    def measure(self):
        voltage = self.voltage_input.value()
        current = self.current_input.value()
        resistance = self.resistance_input.value()

        payload = {
            "