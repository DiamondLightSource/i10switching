#i10accelui.py
#Gui linking to i10plots, straight, simulation
# Contains Gui

# Import libraries

from pkg_resources import require
require('cothread==2.10')
require('scipy==0.10.1')
require('matplotlib==1.3.1')
require('numpy==1.11.1') # is this right?
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

import i10plots
import i10buttons

# Alarm colours
ALARM_BACKGROUND = QtGui.QColor(255, 255, 255)
ALARM_COLORS = [
        QtGui.QColor(  0, 215,  20), # None
        QtGui.QColor(255, 140,   0), # Minor
        QtGui.QColor(255,   0,   0), # Major
        QtGui.QColor(255,   0, 255), # Invalid
        ]


class Gui(QMainWindow):

    UI_FILENAME = 'i10chicgui.ui'

    I10_ADC_1_PV = 'BL10I-EA-USER-01:WAI1'
    I10_ADC_2_PV = 'BL10I-EA-USER-01:WAI2'
    I10_ADC_3_PV = 'BL10I-EA-USER-01:WAI3'
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

        self.ui.simulation = i10plots.Simulation()
        self.ui.gaussians = i10plots.GaussPlot()
        self.toolbar = NavigationToolbar(self.ui.simulation, self)
        self.knobs = i10buttons.Knobs()

        self.ui.graphLayout.addWidget(self.ui.simulation)
        self.ui.graphLayout2.addWidget(self.ui.gaussians)
        self.ui.graphLayout.addWidget(self.toolbar)

        self.ui.small_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(0.1)) # not connected up to the simulation yet # also issue with the simulation radiobutton - need to put them in separate domains or something
        self.ui.full_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(1.0))

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
        self.ui.kplusButton.clicked.connect(lambda: self.simulation_controls(1, 'STEP_K3'))
        self.ui.kminusButton.clicked.connect(lambda: self.simulation_controls(-1, 'STEP_K3'))
        self.ui.bumpleftplusButton.clicked.connect(lambda: self.simulation_controls(1, 'BUMP_LEFT'))
        self.ui.bumpleftminusButton.clicked.connect(lambda: self.simulation_controls(-1, 'BUMP_LEFT'))
        self.ui.bumprightplusButton.clicked.connect(lambda: self.simulation_controls(1, 'BUMP_RIGHT'))
        self.ui.bumprightminusButton.clicked.connect(lambda: self.simulation_controls(-1, 'BUMP_RIGHT'))
        self.ui.bpm1plusButton.clicked.connect(lambda: self.simulation_controls(1, 'BPM1'))
        self.ui.bpm1minusButton.clicked.connect(lambda: self.simulation_controls(-1, 'BPM1'))
        self.ui.bpm2plusButton.clicked.connect(lambda: self.simulation_controls(1, 'BPM2'))
        self.ui.bpm2minusButton.clicked.connect(lambda: self.simulation_controls(-1, 'BPM2'))
        self.ui.scaleplusButton.clicked.connect(lambda: self.simulation_controls(1, 'SCALE'))
        self.ui.scaleminusButton.clicked.connect(lambda: self.simulation_controls(-1, 'SCALE'))
#        self.ui.scaleminusButton.setStyleSheet("background-color: red")

        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.resetButton.setEnabled(False)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.simulation.update_colourin()

        self.ui.gaussians.display()
        self.ui.gaussians.gaussian(2.5, 900)

        self.ui.simButton.setChecked(False)
        self.ui.simButton.clicked.connect(self.toggle_simulation)

    def toggle_simulation(self):
        enabled = self.ui.simButton.isChecked()
        self.ui.resetButton.setEnabled(enabled)

        if self.ui.simButton.isChecked() == True:
            for button, function in zip(self.buttons, self.beam_controls):
                button.clicked.disconnect(function)
        else:
            self.reset()
            for button, function in zip(self.buttons, self.beam_controls):
                button.clicked.connect(function)

    def simulation_controls(self, factor, which_button):
        self.ui.simulation.info.magnets.buttons(factor, which_button)
        self.ui.simulation.ax.collections.remove(self.ui.simulation.fill1)
        self.ui.simulation.ax.collections.remove(self.ui.simulation.fill2)
        self.ui.simulation.update_colourin()

    def k3_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                i10buttons.ButtonData.SHIFT['STEP_K3'])

    def k3_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                -i10buttons.ButtonData.SHIFT['STEP_K3'])

    def bump1_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                i10buttons.ButtonData.SHIFT['BUMP_LEFT'])

    def bump1_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                -i10buttons.ButtonData.SHIFT['BUMP_LEFT'])

    def bump2_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                i10buttons.ButtonData.SHIFT['BUMP_RIGHT'])

    def bump2_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                -i10buttons.ButtonData.SHIFT['BUMP_RIGHT'])

    def hbpm1_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                i10buttons.ButtonData.SHIFT['BPM1'])

    def hbpm1_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                -i10buttons.ButtonData.SHIFT['BPM1'])

    def hbpm2_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                i10buttons.ButtonData.SHIFT['BPM2'])

    def hbpm2_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                -i10buttons.ButtonData.SHIFT['BPM2'])

    def scale_plus(self):
        self.jog_handler(
               [name + ':SETWFSCA' for name in i10buttons.Knobs.NAMES],
                i10buttons.ButtonData.SHIFT['SCALE'])
        self.jog_handler(
               [ctrl + ':WFSCA' for ctrl in i10buttons.Knobs.CTRLS],
                i10buttons.ButtonData.SHIFT['SCALE'])

    def scale_minus(self):
        self.jog_handler(
               [name + ':SETWFSCA' for name in i10buttons.Knobs.NAMES],
                -i10buttons.ButtonData.SHIFT['SCALE'])
        self.jog_handler(
               [ctrl + ':WFSCA' for ctrl in i10buttons.Knobs.CTRLS],
                -i10buttons.ButtonData.SHIFT['SCALE'])

    def reset(self):
        self.ui.simulation.info.magnets.reset()
        self.ui.simulation.ax.collections.remove(self.ui.simulation.fill1)
        self.ui.simulation.ax.collections.remove(self.ui.simulation.fill2)
        self.ui.simulation.update_colourin()

    def flash_table_cell(self, row, column):
        '''Flash a cell twice, with the major alarm color'''
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

    def jog_handler(self, pvs, ofs):
        """
        Wrap the Knobs.jog method to provide exception handling
        in callbacks.
        """
        try:
            self.knobs.jog(pvs, ofs)
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

    def set_jog_scaling(self, scale):
        """Change the scaling applied to magnet corrections."""
        i10buttons.jog_scale = scale

    def setup_table(self):
        '''Initalise all values required for the currents table'''

        VERTICAL_HEADER_SIZE = 38  # Just enough for two lines of text

        table = self.ui.table_widget

        # Initilase items in all table cells
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
        max_pvs = [name + ':IMAX' for name in i10buttons.Knobs.NAMES]
        min_pvs = [name + ':IMIN' for name in i10buttons.Knobs.NAMES]
        offset_pvs = [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS]
        seti_pvs = [name + ':SETI' for name in i10buttons.Knobs.NAMES]
        camonitor(max_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.MAX))
        camonitor(min_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.MIN))
        camonitor(offset_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.OFFSET))
        camonitor(seti_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.SETI))

        # Callbacks: Alarm status for each IOC
        alarm_pvs = [name + ':ERRGSTR' for name in i10buttons.Knobs.NAMES]
        camonitor(alarm_pvs,
                lambda x, i: self.update_alarm(x, i, self.Columns.ERRORS),
                format=FORMAT_TIME)

        # Callbacks: High and low values store PVs in a cache for calculations
        self.cache_pvs = (
                [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS] +
                [ctrl + ':WFSCA' for ctrl in i10buttons.Knobs.CTRLS])
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
        item.setForeground(QtGui.QBrush(ALARM_COLORS[var.severity]))
        item.setBackground(QtGui.QBrush(ALARM_BACKGROUND))
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


