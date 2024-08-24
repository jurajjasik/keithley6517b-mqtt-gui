# GUI applicaption to control Keithley 6517B electrometer over MQTT.

import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui

import sys

from keithley6517b_mqtt_gui import Keithley6517B_MQTT_GUI

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Keithley 6517B MQTT GUI")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("CERN")
    app.setOrganizationDomain("cern.ch")

    window = Keithley6517B_MQTT_GUI()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
