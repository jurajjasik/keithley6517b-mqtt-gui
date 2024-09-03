import json
import logging
import os
import time

from engineering_notation import EngNumber
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget  # Add this line to import QWidget
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .keithley6517b_mqtt_client_logic import Keithley6517B_MQTTClientLogic


def speed_to_nplc(speed):
    if speed == "Fast":
        return 0.01
    elif speed == "Medium":
        return 0.1
    elif speed == "Slow":
        return 1
    elif speed == "High Accuracy":
        return 10
    else:
        return 0.1


def text_to_current_range(text):
    auto_range = True if text == "Auto" else False
    current_range = float(EngNumber(text)) if not auto_range else 0
    return auto_range, current_range


# Initialize status bar with pernament widgets
# see: https://stackoverflow.com/questions/57943862/pyqt5-statusbar-separators
class StatusBarLogic:
    def __init__(self, statusBar):
        self.statusBar = statusBar

        class VLine(QFrame):
            # a simple VLine, like the one you get from designer
            def __init__(self):
                super(VLine, self).__init__()
                self.setFrameShape(self.VLine | self.Sunken)

        # self.statusBar.showMessage("bla-bla bla")

        self.lbl_device = QLabel("Keithley: disconnected")
        # self.lbl_device.setStyleSheet('border: 0; color:  red;')

        self.lbl_mqtt = QLabel("MQTT: disconnected")
        # self.lbl_mqtt.setStyleSheet('border: 0; color:  red;')

        # self.statusBar.reformat()
        # self.statusBar.setStyleSheet('border: 0; background-color: #FFF8DC;')
        # self.statusBar.setStyleSheet("QStatusBar::item {border: none;}")

        self.statusBar.addPermanentWidget(VLine())  # <---
        self.statusBar.addPermanentWidget(self.lbl_device)
        self.statusBar.addPermanentWidget(VLine())  # <---
        self.statusBar.addPermanentWidget(self.lbl_mqtt)
        self.statusBar.addPermanentWidget(VLine())  # <---

    def set_device_status(self, status):
        self.lbl_device.setText(f"Keithley: {status}")

    def set_mqtt_status(self, status):
        self.lbl_mqtt.setText(f"MQTT: {status}")


class Keithley6517B_MQTT_GUI(QMainWindow):
    def __init__(self, config):
        super().__init__()

        self.client_logic = Keithley6517B_MQTTClientLogic(config)

        self.setWindowTitle("Keithley 6517B MQTT GUI")
        self.setWindowIcon(QIcon("icon.png"))

        self.init_ui()

        self.client_logic.start()

    def init_ui(self):
        # Create widgets

        # Measured current label
        self.current_label = QLabel("000.0000 fA")
        self.current_label.setStyleSheet("font-size: 48pt; font-weight: bold;")

        # Shutdown button
        self.shutdown_button = QPushButton("Shutdown")

        # Reset button
        self.reset_button = QPushButton("Reset")

        # Measure button
        self.measure_button = QPushButton("Measure Continuously")

        # Source Voltage Control
        self.source_voltage_label = QLabel("Source Voltage (V)")
        self.source_voltage_ctrl = QDoubleSpinBox()
        self.source_voltage_ctrl.setRange(-1000.0, 1000.0)
        self.source_voltage_ctrl.setSingleStep(0.1)
        self.source_voltage_ctrl.setValue(0.0)

        # Source Voltage Enable Checkbox
        self.source_voltage_enable = QCheckBox("Enable Source Voltage")
        self.source_voltage_enable.setChecked(False)

        # Current range control
        self.current_range_label = QLabel("Current Range (A)")
        self.current_range_value = QLabel()

        # Speed control
        self.speed_label = QLabel("Speed")
        self.speed_ctrl = QComboBox()
        self.speed_ctrl.addItems(["Fast", "Medium", "Slow", "High Accuracy"])

        # Create grid layout
        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to grid
        self.grid.addWidget(self.current_label, 0, 0, 2, 3)

        self.grid.addWidget(self.shutdown_button, 2, 0)
        self.grid.addWidget(self.reset_button, 2, 1)
        self.grid.addWidget(self.measure_button, 2, 2)

        self.grid.addWidget(self.source_voltage_label, 3, 0)
        self.grid.addWidget(self.source_voltage_ctrl, 3, 1)
        self.grid.addWidget(self.source_voltage_enable, 3, 2)

        self.grid.addWidget(self.current_range_label, 4, 0)
        self.grid.addWidget(self.current_range_value, 4, 1)

        self.grid.addWidget(self.speed_label, 5, 0)
        self.grid.addWidget(self.speed_ctrl, 5, 1)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(self.grid)

        self.status_bar_logic = StatusBarLogic(self.statusBar())

        self.status_bar_logic.set_device_status("diconnected")
        self.status_bar_logic.set_mqtt_status("diconnected")

        # attach signals
        self.source_voltage_ctrl.valueChanged.connect(self.on_voltage_input_changed)
        self.source_voltage_enable.stateChanged.connect(
            self.on_source_voltage_enable_changed
        )
        self.shutdown_button.clicked.connect(self.on_shutdown_button_clicked)
        self.reset_button.clicked.connect(self.on_reset_button_clicked)
        self.measure_button.clicked.connect(self.on_measure_button_clicked)
        self.speed_ctrl.currentIndexChanged.connect(self.on_speed_changed)

        self.client_logic.device_status_changed.connect(self.on_device_status_changed)
        self.client_logic.mqtt_status_changed.connect(self.on_mqtt_status_changed)
        self.client_logic.signal_current.connect(self.on_measured_current_changed)
        self.client_logic.signal_state.connect(self.on_state_changed)

    def publish_measure(self):
        nplc = speed_to_nplc(self.speed_ctrl.currentText())
        self.client_logic.publish_measure(nplc, 0, True)

    def on_voltage_input_changed(self, value):
        self.client_logic.publish_source_voltage(value)

    def on_source_voltage_enable_changed(self, state):
        self.client_logic.publish_source_voltage_enable(
            self.source_voltage_enable.isChecked()
        )

    def on_shutdown_button_clicked(self):
        self.client_logic.publish_shutdown()

    def on_reset_button_clicked(self):
        self.client_logic.publish_reset()

    def on_measure_button_clicked(self):
        self.publish_measure()

    def on_current_range_changed(self, index):
        self.publish_measure()

    def on_speed_changed(self, index):
        self.publish_measure()

    def on_device_status_changed(self, status):
        self.status_bar_logic.set_device_status(status)

    def on_mqtt_status_changed(self, status):
        self.status_bar_logic.set_mqtt_status(status)

    def on_measured_current_changed(self, current):
        try:
            current_str = str(EngNumber(current, precision=4))
        except:
            current_str = str(current)
        self.current_label.setText(current_str)

    def on_state_changed(self, state):
        if "source_voltage" in state:
            # disable signal to prevent infinite loop
            self.source_voltage_ctrl.valueChanged.disconnect(
                self.on_voltage_input_changed
            )
            self.source_voltage_ctrl.setValue(state["source_voltage"])
            self.source_voltage_ctrl.valueChanged.connect(self.on_voltage_input_changed)

        if "source_voltage_enable" in state:
            # disable signal to prevent infinite loop
            self.source_voltage_enable.stateChanged.disconnect(
                self.on_source_voltage_enable_changed
            )
            self.source_voltage_enable.setChecked(state["source_voltage_enable"])
            self.source_voltage_enable.stateChanged.connect(
                self.on_source_voltage_enable_changed
            )

        if "current_range" in state:
            # disable signal to prevent infinite loop
            self.current_range_value.setText(str(EngNumber(state["current_range"])))

        if "nplc" in state:
            nplc = state["nplc"]
            speed = (
                "Fast"
                if nplc == 0.01
                else (
                    "Medium"
                    if nplc == 0.1
                    else "Slow" if nplc == 1 else "High Accuracy"
                )
            )
            # disable signal to prevent infinite loop
            self.speed_ctrl.currentIndexChanged.disconnect(self.on_speed_changed)
            self.speed_ctrl.setCurrentText(speed)
            self.speed_ctrl.currentIndexChanged.connect(self.on_speed_changed)

        if "auto_range" in state:
            auto_range = state["auto_range"]
            # disable signal to prevent infinite loop
            self.current_range_value.setText(
                "Auto"
                if auto_range
                else str(EngNumber(state["current_range"])) if "current_range" in state else "Auto"
            )
