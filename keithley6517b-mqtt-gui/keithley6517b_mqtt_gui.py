import json
import logging
import os
import time

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

        self.setWindowTitle("Keithley 6517B MQTT GUI")
        self.setWindowIcon(QIcon("icon.png"))

        self.init_ui()

        self.client_logic = Keithley6517B_MQTTClientLogic(config)
        self.client_logic.start()

    def init_ui(self):
        # Create widgets
        # Source Voltage Control
        self.source_voltage_label = QLabel("Source Voltage (V)")
        self.source_voltage_ctrl = QDoubleSpinBox()
        self.source_voltage_ctrl.setRange(-1000.0, 1000.0)
        self.source_voltage_ctrl.setSingleStep(0.1)
        self.source_voltage_ctrl.setValue(0.0)

        # Create grid layout
        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        # add widgets to grid
        self.grid.addWidget(self.source_voltage_label, 0, 0)
        self.grid.addWidget(self.source_voltage_ctrl, 0, 1)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(self.grid)

        self.status_bar_logic = StatusBarLogic(self.statusBar())

        self.status_bar_logic.set_device_status("diconnected")
        self.status_bar_logic.set_mqtt_status("diconnected")

        # attach signals
        self.source_voltage_ctrl.valueChanged.connect(self.on_voltage_input_changed)

    def on_voltage_input_changed(self, value):
        self.client_logic.publish_source_voltage(value)
