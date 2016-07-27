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

        self.straight = i10straight.Straight()
        self.pv_monitor = i10controls.PvMonitors.get_instance()
        self.knobs = i10buttons.MagnetCoordinator()
        self.simulation = i10plots.Simulation(self.straight)
        self.toolbar = NavigationToolbar(self.simulation, self)

        """Connect buttons to PVs."""
        self.buttons = [self.ui.kplusButton, self.ui.kminusButton,
                   self.ui.bumpleftplusButton, self.ui.bumpleftminusButton,
                   self.ui.bumprightplusButton, self.ui.bumprightminusButton,
                   self.ui.bpm1plusButton, self.ui.bpm1minusButton,
                   self.ui.bpm2plusButton, self.ui.bpm2minusButton,
                   self.ui.scaleplusButton, self.ui.scaleminusButton]

        self.beam_controls = [self.k3_plus, self.k3_minus, self.bump1_plus,
                     self.bump1_minus, self.bump2_plus, self.bump2_minus,
                     self.hbpm1_plus, self.hbpm1_minus, self.hbpm2_plus,
                     self.hbpm2_minus, self.scale_plus, self.scale_minus]

        for button, function in zip(self.buttons, self.beam_controls):
            button.clicked.connect(function)

        self.ui.simButton.setChecked(False)
        self.ui.simButton.clicked.connect(self.toggle_simulation)
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.resetButton.setEnabled(False)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.small_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(0.1))
        self.ui.full_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(1.0))

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

    def jog_handler(self, old_values, ofs, factor):

        """
        Wrap the MagnetCoordinator.jog method to provide exception handling
        in callbacks; update pvs and simulation values.
        """

        if self.ui.simButton.isChecked() == False:
            try:
                jog_values = self.knobs.jog(old_values, ofs, factor)
                self.pv_monitor.set_new_pvs(pvs, jog_values)
                self.simulation_controls(ofs, factor)
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
        else:
            self.simulation_controls(ofs, factor)

    def set_jog_scaling(self, scale): # To be extended
        """Change the scaling applied to magnet corrections."""
        self.knobs.jog_scale = scale

    def toggle_simulation(self):

        """
        Toggle in and out of simulation mode: switch between PVs and
        simulated magnet values, update graph accordingly and change
        background colour to indicate simulation mode enabled.
        """

        enabled = self.ui.simButton.isChecked()
        self.ui.resetButton.setEnabled(enabled)

        if self.ui.simButton.isChecked() == True:
            self.straight.switch_to_sim = True
            self.update_shading()
            self.simulation.figure.patch.set_alpha(0.5)
        else:
            self.straight.switch_to_sim = False
            self.update_shading()
            self.simulation.figure.patch.set_alpha(0.0)

    def simulation_controls(self, ofs, factor):

        """Update values of simulated offsets and scales."""

        self.knobs.sim_offsets_scales(ofs, factor)
        self.update_shading()

    """
    Methods linking buttons to offset/scale values for adjusting PVs
    and simulated values.
    """

    def k3_plus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'STEP_K3', 1)

    def k3_minus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'STEP_K3', -1)

    def bump1_plus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'BUMP_LEFT', 1)

    def bump1_minus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'BUMP_LEFT', -1)

    def bump2_plus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'BUMP_RIGHT', 1)

    def bump2_minus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'BUMP_RIGHT', -1)

    def hbpm1_plus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'BPM1', 1)

    def hbpm1_minus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'BPM1', -1)

    def hbpm2_plus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'BPM2', 1)

    def hbpm2_minus(self):
        self.jog_handler(self.pv_monitor.get_offsets(), 'BPM2', -1)

    def scale_plus(self):
        self.jog_handler(self.pv_monitor.get_set_scales(), 'SET_SCALE', 1)
        self.jog_handler(self.pv_monitor.get_scales(), 'SCALE', 1)

    def scale_minus(self):
        self.jog_handler(self.pv_monitor.get_set_scales(), 'SET_SCALE', -1)
        self.jog_handler(self.pv_monitor.get_scales(), 'SCALE', -1)

    def reset(self): # keep this here or pointless extra??

        """
        Reset the offsets and scales to the starting point, only whilst in
        simulation mode. Does not affect the PVs.
        """

        self.knobs.sim_reset()
        self.update_shading()

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


def main():
    cothread.iqt()
    the_ui = Gui()
    the_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()


