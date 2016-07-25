#!/usr/bin/env dls-python2.7
#i10accelui.py
#Gui linking to i10plots, straight, simulation
# Contains Gui

# Import libraries

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
from PyQt4 import uic
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import QMainWindow
import os
import traceback
import numpy as np

import i10plots
import i10buttons
import i10straight

# THIS IS TEMPORARY UNTIL I WORK OUT THE BEST PLACE TO KEEP THEM
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

        self.setup_table()

        self.straight = i10straight.Straight()
        self.knobs = i10buttons.Knobs(self.straight)

        # Connect buttons to PVs
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

        # Connect buttons to simulation
        self.ui.kplusButton.clicked.connect(lambda:
                                     self.simulation_controls(1, 'STEP_K3'))
        self.ui.kminusButton.clicked.connect(lambda:
                                     self.simulation_controls(-1, 'STEP_K3'))
        self.ui.bumpleftplusButton.clicked.connect(lambda:
                                     self.simulation_controls(1, 'BUMP_LEFT'))
        self.ui.bumpleftminusButton.clicked.connect(lambda:
                                     self.simulation_controls(-1, 'BUMP_LEFT'))
        self.ui.bumprightplusButton.clicked.connect(lambda:
                                     self.simulation_controls(1, 'BUMP_RIGHT'))
        self.ui.bumprightminusButton.clicked.connect(lambda:
                                     self.simulation_controls(-1, 'BUMP_RIGHT'))
        self.ui.bpm1plusButton.clicked.connect(lambda:
                                     self.simulation_controls(1, 'BPM1'))
        self.ui.bpm1minusButton.clicked.connect(lambda:
                                     self.simulation_controls(-1, 'BPM1'))
        self.ui.bpm2plusButton.clicked.connect(lambda:
                                     self.simulation_controls(1, 'BPM2'))
        self.ui.bpm2minusButton.clicked.connect(lambda:
                                     self.simulation_controls(-1, 'BPM2'))
#        self.ui.scaleplusButton.clicked.connect(lambda:
#                                     self.simulation_controls(1, 'SCALE'))
#        self.ui.scaleminusButton.clicked.connect(lambda:
#                                     self.simulation_controls(-1, 'SCALE'))
        self.ui.simButton.setChecked(False)
        self.ui.simButton.clicked.connect(self.toggle_simulation)
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.resetButton.setEnabled(False)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.small_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(0.1))
        self.ui.full_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(1.0))

#        self.offset = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        camonitor(i10buttons.Knobs.BURT_STATUS_PV, self.update_burt_led)
        camonitor(i10buttons.Knobs.MAGNET_STATUS_PV,
                self.update_magnet_led, format=FORMAT_CTRL)
        camonitor(i10buttons.Knobs.CYCLING_STATUS_PV,
                self.update_cycling_textbox, format=FORMAT_CTRL)

        self.simulation = i10plots.Simulation(self.straight)
        self.toolbar = NavigationToolbar(self.simulation, self)

        self.ui.matplotlib_layout.addWidget(self.simulation)
        self.ui.matplotlib_layout.addWidget(self.toolbar)

        self.simulation.update_colourin()
        self.simulation.magnet_limits()

#    def store_settings(self, button):
#        self.offset += np.array(button)*self.knobs.jog_scale

    def jog_handler(self, pvs, old_values, ofs, factor):
        """
        Wrap the Knobs.jog method to provide exception handling
        in callbacks.
        """
        if self.ui.simButton.isChecked() == False:
            try:
                jog_pvs = self.knobs.jog(pvs, old_values, ofs, factor)
                self.straight.controls.set_new_pvs(jog_pvs[0], jog_pvs[1])
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
            print 'Simulation mode' ######################################################################################
            self.knobs.sim_offsets(ofs, factor)
            self.simulation.ax.collections.remove(self.simulation.fill1)
            self.simulation.ax.collections.remove(self.simulation.fill2)
            self.simulation.update_colourin()


    def set_jog_scaling(self, scale):
        """Change the scaling applied to magnet corrections."""
        self.knobs.jog_scale = scale

    def toggle_simulation(self): # THIS NEEDS SOME WORK
        enabled = self.ui.simButton.isChecked()
        self.ui.resetButton.setEnabled(enabled)

        if self.ui.simButton.isChecked() == True:
#            for button, function in zip(self.buttons, self.beam_controls):
#                button.clicked.disconnect(function)
            self.straight.switch_to_sim = True
            self.simulation.figure.patch.set_alpha(0.5)
        else:
#            self.reconfigure(self.straight.offsets) # RETURN TO CAMONITORED VALUE
#            for button, function in zip(self.buttons, self.beam_controls):
#                button.clicked.connect(function)
            self.straight.switch_to_sim = False
            self.simulation.figure.patch.set_alpha(0.0)

    def simulation_controls(self, factor, which_button):
        print 'Need to disconnect this' ######################################################################################
#        self.knobs.sim_offsets(factor, which_button)
#        self.simulation.ax.collections.remove(self.simulation.fill1)
#        self.simulation.ax.collections.remove(self.simulation.fill2)
#        self.simulation.update_colourin()

    def k3_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'STEP_K3', 1)

    def k3_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'STEP_K3', -1)

    def bump1_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS], #names of camonitored values - probably nicer way to do this but leave for now
                self.straight.offsets, #camonitored values
                'BUMP_LEFT', 1)

    def bump1_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'BUMP_LEFT', -1)

    def bump2_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'BUMP_RIGHT', 1)

    def bump2_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'BUMP_RIGHT', -1)

    def hbpm1_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'BPM1', 1)

    def hbpm1_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'BPM1', -1)

    def hbpm2_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'BPM2', 1)

    def hbpm2_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in CTRLS],
                self.straight.offsets,
                'BPM2', -1)

    def scale_plus(self): # am I doing the simulation right for this??
        self.jog_handler(
               [name + ':SETWFSCA' for name in NAMES],
                self.straight.set_scales,
                'SCALE', 1)
        self.jog_handler(
               [ctrl + ':WFSCA' for ctrl in CTRLS],
                self.straight.scales,
                'SCALE', 1)

    def scale_minus(self):
        self.jog_handler(
               [name + ':SETWFSCA' for name in NAMES],
                self.straight.set_scales,
                'SCALE', -1)
        self.jog_handler(
               [ctrl + ':WFSCA' for ctrl in CTRLS],
                self.straight.scales,
                'SCALE', -1)

    def reset(self):
        self.knobs.sim_reset()
        self.simulation.ax.collections.remove(self.simulation.fill1)
        self.simulation.ax.collections.remove(self.simulation.fill2)
        self.simulation.update_colourin()

    def reconfigure(self, value): #not currently right
        self.knobs.sim_reconfigure(value)
        self.simulation.ax.collections.remove(self.simulation.fill1)
        self.simulation.ax.collections.remove(self.simulation.fill2)
        self.simulation.update_colourin()

    def update_cycling_textbox(self, var):
        '''Updates cycling status from enum attached to pv'''
        self.ui.cycling_textbox_2.setText(QtCore.QString('%s' % var.enums[var]))

    def update_magnet_led(self, var):
        '''Uses PV alarm status to choose color for qframe'''
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, i10buttons.ALARM_COLORS[var.severity])
        self.ui.magnet_led_2.setPalette(palette)

    def update_burt_led(self, var):
        '''Uses burt valid PV to determine qframe color'''
        palette = QtGui.QPalette()

        # BURT PV is one if okay, zero if bad:
        #    set no alarm (0) or major alarm(2)
        alarm_state = 0 if var == 1 else 2

        palette.setColor(QtGui.QPalette.Background, i10buttons.ALARM_COLORS[alarm_state])
        self.ui.burt_led_2.setPalette(palette)

    def flash_table_cell(self, row, column):
        '''Flash a cell twice, with the major alarm color'''
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
        '''Initalise all values required for the currents table'''

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
        '''Updates a table widget populated with a float'''
        item = self.ui.table_widget.item(row, col)
        item.setText(QtCore.QString('%.3f' % var))

    def update_alarm(self, var, row, col):
        '''Updates an alarm sensitive table widget'''
        item = self.ui.table_widget.item(row, col)
        item.setForeground(QtGui.QBrush(i10buttons.ALARM_COLORS[var.severity]))
        item.setBackground(QtGui.QBrush(i10buttons.ALARM_BACKGROUND))
        item.setText(QtCore.QString(var))

    def update_cache(self, var, dummy):
        '''
        Called by camonitor. Updates values in the cache and uses
        them to provide new high and low values to the table
        '''
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


