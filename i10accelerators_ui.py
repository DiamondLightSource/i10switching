#!/usr/bin/env dls-python2.7
# i10accelerators_ui.py
# Gui linking to i10plots, straight, simulation
# Contains Gui

"""
Buttons to move I10 fast chicane magnet offsets and scales.
Provides a gui to control magnet scaling and offsets in order
to allow independant steering of photon and electron beams to
maintain a closed bump and a simulation of the beamline that
indicates the effects of changes to the scaling and offsets.
"""

from pkg_resources import require
require('numpy==1.11.1')
require('scipy==0.10.1')
require('matplotlib==1.3.1')
require('cothread==2.13')

import sys
import cothread
from cothread.catools import *
from matplotlib.backends.backend_qt4agg import (
    NavigationToolbar2QT as NavigationToolbar)
from PyQt4 import uic, QtGui, QtCore
from PyQt4.QtGui import QMainWindow
import os
import traceback
import numpy as np

import i10plots
import i10buttons
import i10straight
import i10controls

# THIS IS TEMPORARY
NAMES = [
    'SR09A-PC-FCHIC-01',
    'SR09A-PC-FCHIC-02',
    'SR10S-PC-FCHIC-03',
    'SR10S-PC-FCHIC-04',
    'SR10S-PC-FCHIC-05']

CTRLS = [
    'SR09A-PC-CTRL-01',
    'SR09A-PC-CTRL-02',
    'SR10S-PC-CTRL-03',
    'SR10S-PC-CTRL-04',
    'SR10S-PC-CTRL-05']

class Gui(QMainWindow):

    """
    GUI containing a simulation of the beamline and buttons
    to control the beam and/or simulation. Relevant status 
    information is also gathered from PVs and shown to the user
    in a table.
    """

    UI_FILENAME = 'i10chicgui.ui'
    HIGHLIGHT_COLOR = QtGui.QColor(235, 235, 235) # Light grey

    class Columns(object):
        MAX=0
        HIGH=1
        OFFSET=2
        SETI=3
        LOW=4
        MIN=5
        ERRORS=6

    def __init__(self):
        QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), self.UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.parent = QtGui.QMainWindow()

        self.setup_table() # THIS NEEDS TO BE MOVED/AMALGAMATED WITH CAMONITORED VALUES IN I10CONTROLS

#        self.jog_buttons = JogButtonHandler()

        self.straight = i10straight.Straight()
        self.pv_monitor = i10controls.PvMonitors.get_instance()
        self.knobs = i10buttons.MagnetCoordinator()


        self.simcontrol = i10straight.SimModeController()
        self.realcontrol = i10straight.RealModeController()
        self.realcontrol.register_straight(self.straight)

        self.pv_writer = i10controls.PvWriter()
        self.sim_writer = i10controls.SimWriter()
        self.writer = self.pv_writer

        self.sim_writer.register_controller(self.simcontrol.update_sim) #################### moved this in here so that correct instance of everything

        self.simulation = i10plots.Simulation(self.straight)
        self.toolbar = NavigationToolbar(self.simulation, self)

        self.jog_scale = 1.0

        """Connect buttons to PVs."""
        self.ui.kplusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.STEP_K3, 1)) # add jog_buttons if move jog_handler to another class
        self.ui.kminusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.STEP_K3, -1))
        self.ui.bumpleftplusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.BUMP_LEFT, 1))
        self.ui.bumpleftminusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.BUMP_LEFT, -1))
        self.ui.bumprightplusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.BUMP_RIGHT, 1))
        self.ui.bumprightminusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.BUMP_RIGHT, -1))
        self.ui.bpm1plusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.BPM1, 1))
        self.ui.bpm1minusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.BPM1, -1))
        self.ui.bpm2plusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.BPM2, 1))
        self.ui.bpm2minusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.BPM2, -1))
        self.ui.scaleplusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.SCALE, 1))
        self.ui.scaleminusButton.clicked.connect(lambda: self.jog_handler(i10buttons.Moves.SCALE, -1))

        self.ui.simButton.setChecked(False)
        self.ui.simButton.clicked.connect(self.toggle_simulation)
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.resetButton.setEnabled(False)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.jog_scale_slider.valueChanged.connect(self.set_jog_scaling)
        self.ui.jog_scale_textbox.setText(str(self.jog_scale))

        """Monitor the states of magnets, BURT and cycling."""
        camonitor(i10buttons.MagnetCoordinator.BURT_STATUS_PV, self.update_burt_led)
        camonitor(i10buttons.MagnetCoordinator.MAGNET_STATUS_PV,
                  self.update_magnet_led, format=FORMAT_CTRL)
        camonitor(i10buttons.MagnetCoordinator.CYCLING_STATUS_PV,
                  self.update_cycling_textbox, format=FORMAT_CTRL)

        """Add simulation and toolbar to the GUI."""
        self.ui.matplotlib_layout.addWidget(self.simulation)
        self.ui.matplotlib_layout.addWidget(self.toolbar)

        """
        Add shading to indicate ranges over which photon beams sweep, and
        dotted lines indicating limits of magnet tolerances.
        """
        self.simulation.update_colourin()
#        self.simulation.magnet_limits()

    def set_jog_scaling(self):
        """Change the scaling applied to magnet corrections."""
        self.jog_scale = self.ui.jog_scale_slider.value() * 0.1
        self.ui.jog_scale_textbox.setText(str(self.jog_scale))

    def toggle_simulation(self):

        """
        Toggle in and out of simulation mode: switch between PVs and
        simulated magnet values, update graph accordingly and change
        background colour to indicate simulation mode enabled.
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

        self.simulation.ax.collections.remove(self.simulation.fill1)
        self.simulation.ax.collections.remove(self.simulation.fill2)
        self.simulation.update_colourin()

    def update_cycling_textbox(self, var):
        """Update cycling status from enum attached to PV."""
        self.ui.cycling_textbox_2.setText(QtCore.QString('%s' % var.enums[var]))

    def update_magnet_led(self, var):
        """Use PV alarm status to choose color for qframe."""
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, i10buttons.ALARM_COLORS[var.severity])
        self.ui.magnet_led_2.setPalette(palette)

    def update_burt_led(self, var):
        """Use burt valid PV to determine qframe colour."""
        palette = QtGui.QPalette()

        # BURT PV is one if okay, zero if bad:
        #    set no alarm (0) or major alarm(2)
        alarm_state = 0 if var == 1 else 2

        palette.setColor(QtGui.QPalette.Background, i10buttons.ALARM_COLORS[alarm_state])
        self.ui.burt_led_2.setPalette(palette)

    def flash_table_cell(self, row, column):

        """Flash a cell twice with the major alarm colour."""

        table = self.ui.table_widget
        item = table.item(column, row)

        item.setBackground(QtGui.QBrush(i10buttons.ALARM_COLORS[2]))
        QtCore.QTimer.singleShot(
                200, lambda: item.setBackground(QtGui.QBrush(i10buttons.ALARM_BACKGROUND)))
        QtCore.QTimer.singleShot(
                400, lambda: item.setBackground(QtGui.QBrush(i10buttons.ALARM_COLORS[2])))
        QtCore.QTimer.singleShot(
                600, lambda: item.setBackground(QtGui.QBrush(i10buttons.ALARM_BACKGROUND)))
        QtCore.QTimer.singleShot(
                800, lambda: item.setBackground(QtGui.QBrush(i10buttons.ALARM_COLORS[2])))
        QtCore.QTimer.singleShot(
                900, lambda: item.setBackground(QtGui.QBrush(i10buttons.ALARM_BACKGROUND)))

    def setup_table(self):

        """Initialise all values required for the currents table."""
        # TODO: Use PvMonitors to get the values and updated for the table
        VERTICAL_HEADER_SIZE = 38  # Just enough for two lines of text

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

        # Callbacks: Min and Max
        max_pvs = [name + ':IMAX' for name in NAMES]
        min_pvs = [name + ':IMIN' for name in NAMES]
        offset_pvs = [ctrl + ':OFFSET' for ctrl in CTRLS]
        seti_pvs = [name + ':SETI' for name in NAMES]
        camonitor(max_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.MAX))
        camonitor(min_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.MIN))
        camonitor(offset_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.OFFSET))
        camonitor(seti_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.SETI))

        # Callbacks: Alarm status for each IOC
        alarm_pvs = [name + ':ERRGSTR' for name in NAMES]
        camonitor(alarm_pvs,
                lambda x, i: self.update_alarm(x, i, self.Columns.ERRORS),
               format=FORMAT_TIME)

        # Callbacks: High and low values store PVs in a cache for calculations
        self.cache_pvs = (
                [ctrl + ':OFFSET' for ctrl in CTRLS] +
                [ctrl + ':WFSCA' for ctrl in CTRLS])
        self.cache = c = {}
        for i in range(1, 6):
            c['%02d' % i] = {}
        for pv in self.cache_pvs:
            c[pv.split(':')[0][-2:]][pv.split(':')[1]] = caget(pv)
        camonitor(self.cache_pvs, self.update_cache)

    def update_float(self, var, row, col):
        """Updates a table widget populated with a float."""
        item = self.ui.table_widget.item(row, col)
        item.setText(QtCore.QString('%.3f' % var))

    def update_alarm(self, var, row, col):
        """Updates an alarm sensitive table widget."""
        item = self.ui.table_widget.item(row, col)
        item.setForeground(QtGui.QBrush(i10buttons.ALARM_COLORS[var.severity]))
        item.setBackground(QtGui.QBrush(i10buttons.ALARM_BACKGROUND))
        item.setText(QtCore.QString(var))

    def update_cache(self, var, dummy):
        """
        Called by camonitor. Updates values in the cache and uses
        them to provide new high and low values to the table.
        """
        ioc_1 = var.name.split(':')[0][-2:]
        ioc_2 = var.name.split(':')[1]
        c = self.cache[ioc_1]
        c[ioc_2] = var
        high = c['OFFSET'] + c['WFSCA']
        low = c['OFFSET'] - c['WFSCA']
        self.update_float(high, int(ioc_1)-1, self.Columns.HIGH)
        self.update_float(low, int(ioc_1)-1, self.Columns.LOW)

#class JogButtonHandler(object): #try amalgamating this with class above

    """ When button clicked this class sends information about which button was
    clicked to either PvWriter or SimWriter depending on whether simulation-only
    mode is enabled."""

#    def __init__(self):

#        self.writer = i10controls.PvWriter()

    def jog_handler(self, key, factor):

        """
        Wrap the MagnetCoordinator.jog method to provide exception handling
        in callbacks; update pvs and simulation values.
        """

        try:
            self.writer.write(key, factor, self.jog_scale)
            self.update_shading()

        except i10buttons.OverCurrentException, e:
            self.flash_table_cell(self.Columns.OFFSET, e.magnet_index)
        except (cothread.catools.ca_nothing, cothread.cadef.CAException), e:
            print 'Cothread Exception:', e
            msgBox = QtGui.QMessageBox(self.parent)
            msgBox.setText('Cothread Exception: %s' % e)
            msgBox.exec_()
        except Exception, e:
            print 'Unexpected Exception:', e
            msgBox = QtGui.QMessageBox(self.parent)
            msgBox.setText('Unexpected Exception: %s' % e)
            msgBox.setInformativeText(traceback.format_exc(3))
            msgBox.exec_()


    def reset(self):

        """
        Reset the offsets and scales to the starting point, only whilst in
        simulation mode. Does not affect the PVs.
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


