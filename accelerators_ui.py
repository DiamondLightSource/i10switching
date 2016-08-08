#!/usr/bin/env dls-python2.7
# accelerators_ui.py
# Gui linking to plots, magnet_jogs, straight, controls, writers
# Contains Gui

"""
Buttons to move I10 fast chicane magnet offsets and scales.

Provides a gui to control magnet scaling and offsets in order
to allow independent steering of photon and electron beams to
maintain a closed bump and a simulation of the beamline that
indicates the effects of changes to the scaling and offsets.
"""

from pkg_resources import require
require('numpy>=1.10.1')
require('scipy>=0.10.1')
require('matplotlib==1.3.1')
require('cothread==2.13')

import sys
import cothread
from cothread.catools import camonitor, FORMAT_CTRL
from matplotlib.backends.backend_qt4agg import (
    NavigationToolbar2QT as NavigationToolbar)
from PyQt4 import uic, QtGui, QtCore
from PyQt4.QtGui import QMainWindow
import os
import traceback

import plots
import magnet_jogs
import straight
import controls
import writers


# Alarm colours
ALARM_BACKGROUND = QtGui.QColor(255, 255, 255)
ALARM_COLORS = [
        QtGui.QColor(0, 215, 20), # None
        QtGui.QColor(255, 140, 0), # Minor
        QtGui.QColor(255, 0, 0), # Major
        QtGui.QColor(255, 0, 255), # Invalid
        ]


class Gui(QMainWindow):

    """
    GUI for the accelerator physicists.

    GUI containing a simulation of the beamline and buttons
    to control the beam and/or simulation. Relevant status
    information is also gathered from PVs and shown to the user
    in a table.
    """

    UI_FILENAME = 'acceleratorui.ui'
    HIGHLIGHT_COLOR = QtGui.QColor(235, 235, 235) # Light grey

    class Columns(object):
        MAX = 0
        HIGH = 1
        OFFSET = 2
        SETI = 3
        LOW = 4
        MIN = 5
        ERRORS = 6

    def __init__(self):
        """Initialise GUI."""
        QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), self.UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.parent = QtGui.QMainWindow()

        # Get instances of required classes.
        self.straight = straight.Straight()
        self.pv_monitor = controls.PvMonitors.get_instance()
        self.simcontrol = straight.SimModeController()
        self.realcontrol = straight.RealModeController()
        self.pv_writer = writers.PvWriter()
        self.sim_writer = writers.SimWriter(self.simcontrol)

        # Register listeners.
        self.realcontrol.register_straight(self.straight)
        self.pv_monitor.register_straight_listener(self.update_table)

        # Set up simulation, toolbar and table in the GUI.
        self.simulation = plots.Simulation(self.straight)
        self.toolbar = NavigationToolbar(self.simulation, self)
        self.setup_table()

        # Initial settings for GUI: connected to PVs and jog scale = 1.
        self.writer = self.pv_writer
        self.jog_scale = 1.0

        # Connect buttons to PVs.
        self.ui.kplusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.STEP_K3, 1))
        self.ui.kminusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.STEP_K3, -1))
        self.ui.bumpleftplusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.BUMP_LEFT, 1))
        self.ui.bumpleftminusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.BUMP_LEFT, -1))
        self.ui.bumprightplusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.BUMP_RIGHT, 1))
        self.ui.bumprightminusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.BUMP_RIGHT, -1))
        self.ui.bpm1plusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.BPM1, 1))
        self.ui.bpm1minusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.BPM1, -1))
        self.ui.bpm2plusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.BPM2, 1))
        self.ui.bpm2minusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.BPM2, -1))
        self.ui.scaleplusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.SCALE, 1))
        self.ui.scaleminusButton.clicked.connect(
            lambda: self.jog_handler(magnet_jogs.Moves.SCALE, -1))

        self.ui.simButton.setChecked(False)
        self.ui.simButton.clicked.connect(self.toggle_simulation)
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.resetButton.setEnabled(False)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.jog_scale_slider.valueChanged.connect(self.set_jog_scaling)
        self.ui.jog_scale_textbox.setText(str(self.jog_scale))

        # Monitor the states of magnets, BURT and cycling.
        camonitor(controls.PvReferences.BURT_STATUS_PV, self.update_burt_led)
        camonitor(controls.PvReferences.MAGNET_STATUS_PV,
                  self.update_magnet_led, format=FORMAT_CTRL)
        camonitor(controls.PvReferences.CYCLING_STATUS_PV,
                  self.update_cycling_textbox, format=FORMAT_CTRL)

        # Add simulation and toolbar to the GUI.
        self.ui.matplotlib_layout.addWidget(self.simulation)
        self.ui.matplotlib_layout.addWidget(self.toolbar)

        # Add shading to indicate ranges over which photon beams sweep, and
        # dotted lines indicating limits of magnet tolerances.
        self.simulation.update_colourin()
        self.simulation.magnet_limits()

    def set_jog_scaling(self):
        """Change the scaling applied to magnet corrections."""
        self.jog_scale = self.ui.jog_scale_slider.value() * 0.1
        self.ui.jog_scale_textbox.setText(str(self.jog_scale))

    def toggle_simulation(self):
        """
        Toggle in and out of simulation mode.

        Switch between PVs and simulated magnet values,
        update graph accordingly and change background colour
        to indicate simulation mode enabled.
        """
        enabled = self.ui.simButton.isChecked()
        self.ui.resetButton.setEnabled(enabled)

        if enabled:
            self.writer = self.sim_writer
            self.realcontrol.deregister_straight(self.straight)
            self.simcontrol.register_straight(self.straight)
            self.update_shading()
            self.simulation.figure.patch.set_alpha(0.5)
        else:
            self.writer = self.pv_writer
            self.simcontrol.deregister_straight(self.straight)
            self.realcontrol.register_straight(self.straight)
            self.update_shading()
            self.simulation.figure.patch.set_alpha(0.0)

    def update_shading(self):
        """Update the x-ray beam range shading."""
        self.simulation.update_colourin()

    def update_cycling_textbox(self, var):
        """Update cycling status from enum attached to PV."""
        self.ui.cycling_textbox_2.setText(QtCore.QString('%s' % var.enums[var]))

    def update_magnet_led(self, var):
        """Use PV alarm status to choose color for qframe."""
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, ALARM_COLORS[var.severity])
        self.ui.magnet_led_2.setPalette(palette)

    def update_burt_led(self, var):
        """Use burt valid PV to determine qframe colour."""
        palette = QtGui.QPalette()

        # BURT PV is one if okay, zero if bad:
        #    set no alarm (0) or major alarm(2)
        alarm_state = 0 if var == 1 else 2

        palette.setColor(QtGui.QPalette.Background, ALARM_COLORS[alarm_state])
        self.ui.burt_led_2.setPalette(palette)

    def flash_table_cell(self, row, column):
        """Flash a cell twice with the major alarm colour."""
        table = self.ui.table_widget
        item = table.item(column, row)

        item.setBackground(QtGui.QBrush(ALARM_COLORS[2]))
        QtCore.QTimer.singleShot(
                200, lambda: item.setBackground(QtGui.QBrush(ALARM_BACKGROUND)))
        QtCore.QTimer.singleShot(
                400, lambda: item.setBackground(QtGui.QBrush(ALARM_COLORS[2])))
        QtCore.QTimer.singleShot(
                600, lambda: item.setBackground(QtGui.QBrush(ALARM_BACKGROUND)))
        QtCore.QTimer.singleShot(
                800, lambda: item.setBackground(QtGui.QBrush(ALARM_COLORS[2])))
        QtCore.QTimer.singleShot(
                900, lambda: item.setBackground(QtGui.QBrush(ALARM_BACKGROUND)))

    def setup_table(self):
        """Initialise all values required for the currents table."""
        table = self.ui.table_widget

        # Initialise items in all table cells
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = QtGui.QTableWidgetItem(QtCore.QString('No Data'))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                if col in [self.Columns.MAX, self.Columns.MIN]:
                    item.setBackground(QtGui.QBrush(self.HIGHLIGHT_COLOR))
                table.setItem(row, col, item)

        # Automatically adjust table size
        table.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)

    def update_table(self, key, index):
        """When this is called the table values and cache are updated."""
        # TODO: connect table to simulation mode!!
        if key == controls.Arrays.IMAX:
            self.update_float(self.pv_monitor.get_max_currents()[index],
                              index, self.Columns.MAX)

        elif key == controls.Arrays.IMIN:
            self.update_float(self.pv_monitor.get_min_currents()[index],
                            index, self.Columns.MIN)

        elif key == controls.Arrays.OFFSETS:
            self.update_float(self.pv_monitor.get_offsets()[index],
                              index, self.Columns.OFFSET)
            self.update_cache(self.pv_monitor.get_cache(), index)

        elif key == controls.Arrays.SETI:
            self.update_float(self.pv_monitor.get_actual_offsets()[index],
                              index, self.Columns.SETI)

        elif key == controls.Arrays.ERRORS:
            self.update_alarm(self.pv_monitor.get_errors()[index],
                              index, self.Columns.ERRORS)

        elif key == controls.Arrays.SCALES:
            self.update_cache(self.pv_monitor.get_cache(), index)

    def update_float(self, var, row, col):
        """Updates a table widget populated with a float."""
        item = self.ui.table_widget.item(row, col)
        item.setText(QtCore.QString('%.3f' % var))

    def update_alarm(self, var, row, col):
        """Updates an alarm sensitive table widget."""
        item = self.ui.table_widget.item(row, col)
        item.setForeground(QtGui.QBrush(ALARM_COLORS[var.severity]))
        item.setBackground(QtGui.QBrush(ALARM_BACKGROUND))
        item.setText(QtCore.QString(var))

    def update_cache(self, cache, index):
        """Updates cached values of offsets and scales for the table."""
        high = (cache['%02d' % index][controls.Arrays.OFFSETS] +
                cache['%02d' % index][controls.Arrays.SCALES])
        low = (cache['%02d' % index][controls.Arrays.OFFSETS] -
               cache['%02d' % index][controls.Arrays.SCALES])
        self.update_float(high, index, self.Columns.HIGH)
        self.update_float(low, index, self.Columns.LOW)

    def jog_handler(self, key, factor):
        """
        Handle button clicks.

        When button clicked this class sends information to the writer and
        provides exception handling in callbacks.
        """
        try:
            self.writer.write(key, factor * self.jog_scale)
            self.update_shading()

        except magnet_jogs.OverCurrentException, e:
            self.flash_table_cell(self.Columns.OFFSET, e.magnet_index)
        except (cothread.catools.ca_nothing, cothread.cadef.CAException), e:
            print 'Cothread Exception:', e
            msgBox = QtGui.QMessageBox(self.parent)
            msgBox.setText('Cothread Exception: %s' % e)
            msgBox.exec_()
        except StandardError, e:
            print 'Unexpected Exception:', e
            msgBox = QtGui.QMessageBox(self.parent)
            msgBox.setText('Unexpected Exception: %s' % e)
            msgBox.setInformativeText(traceback.format_exc(3))
            msgBox.exec_()

    def reset(self):
        """
        Reset the offsets and scales to the starting point.

        Only whilst in simulation mode. Does not affect the PVs.
        """
        if self.ui.simButton.isChecked():
            self.writer.reset()
            self.update_shading()


def main():
    cothread.iqt()
    the_ui = Gui()
    the_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()
