#!/usr/bin/env dls-python2.7


'''
Buttons to move I10 fast chicane magnet offsets and scales.

Provides a gui to control magnet scaling and offsets
in order to allow independant steering of photon and
electron beams to maintain a closed bump.
'''


from pkg_resources import require
require('cothread==2.10')
require('scipy==0.10.1')
require('matplotlib==1.3.1')
require('numpy==1.11.1')

import cothread
from cothread.catools import caget, caput, camonitor, FORMAT_TIME, FORMAT_CTRL
import numpy
import scipy.io
import os, sys
import traceback

from PyQt4 import QtCore
from PyQt4 import QtGui

from i10 import Ui_i10_knobs

import pylab

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import scipy.integrate as integ

import i10plots

# Alarm colours
ALARM_BACKGROUND = QtGui.QColor(255, 255, 255)
ALARM_COLORS = [
        QtGui.QColor(  0, 215,  20), # None
        QtGui.QColor(255, 140,   0), # Minor
        QtGui.QColor(255,   0,   0), # Major
        QtGui.QColor(255,   0, 255), # Invalid
        ]


class OverCurrentException(Exception):
    def __init__(self, magnet_index):
        self.magnet_index = magnet_index


class Knobs(object):

    '''
    Provides an interface to control the I10 Fast Chicane.
    Values stored in the mat file are obtained through a matlab
    middle layer simulation. The values are calculated to enable
    steering of the photon and electron beams.
    '''

    # Path for matfile loading
    I10_PATH = '/dls_sw/work/common/matlab/i10'

    # PV names
    TRIMNAMES = [
        'SR10I-MO-VSTR-21',
        'SR10I-MO-VSTR-22',
        'SR10I-MO-VSTR-11',
        'SR10I-MO-VSTR-12']
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

    def __init__(self):
        '''Setup physics values from matlab files'''
        S = scipy.io.loadmat(os.path.join(self.I10_PATH, 'knobsi10.mat'))

        # knob deltas
        dbpm = 1e-4  # 1e-4 mm = 100 nm
        dscale = numpy.array([1e-2, 1e-2, 0, 1e-2, 1e-2])
        dk3 = numpy.array([0, 0, 1e-2, 0, 0])

        self.dscale = dscale * 1
        self.dbpm = dbpm * 1
        self.dk3 = dk3 * 1

        ## TODO: pick the correct parts from the file
        self.left = S['ch'][:,0] * dbpm
        self.right = S['ch'][:,1] * dbpm
        self.trimleft = S['tv'][:,0] * dbpm
        self.trimright = S['tv'][:,1] * dbpm

        # 600 Clicks to move through entire range
        self.b1 = numpy.array([23.2610, 23.2145, 10.1888, 0, 0]) / 600
        self.b2 = numpy.array([0, 0, 10.1888, 23.1068, 23.0378]) / 600

        self.jog_scale = 1.0

    def get_imin(self):
        return caget([name + ':IMIN' for name in self.NAMES])

    def get_imax(self):
        return caget([name + ':IMAX' for name in self.NAMES])

    def get_offset(self):
        return caget([ctrl + ':OFFSET' for ctrl in self.CTRLS])

    def get_scale(self):
        return caget([name + ':SETWFSCA' for name in self.NAMES])

    def get_error(self):
        return caget([name + ':ERRG' for name in self.NAMES])

    def jog(self, pvs, ofs):
        '''
        Incremeants the list of PVs by the offset.
        Errors are created when a user is likley to exceed magnet tolerances.
        '''
        ofs = ofs * self.jog_scale

        old_values = caget(pvs)
        values = old_values + ofs;

        print
        for name, old, new in zip(pvs, old_values, values):
            print '%s:\t%f->%f' % (name, old, new);

        scales = [abs(scale) for scale in self.get_scale()]
        offsets = self.get_offset()
        imaxs = self.get_imax()
        imins = self.get_imin()

        # Check errors on limits.
        for n in range(len(pvs)):
            max = imaxs[n]
            min = imins[n]
            offset = offsets[n]
            scale = scales[n]
            new_val = ofs[n]
            high = offset + new_val + scale
            low  = offset + new_val - scale
            if(high > max or low < min):
                print 'Warning: Setting current value above limits:'
                print ('%s: High: %f\tLow: %f\tMin: %f\tMax: %f\n'
                        % (pvs[n], high, low, max, min))
                raise OverCurrentException(n)
        caput(pvs, values)


class KnobsUi(object):

    '''
    Provides the GUI to the underlying Knobs class.
    Relevant status information is also gathered from PVs
    and shown to the user.
    '''

    MAGNET_STATUS_PV = 'SR10I-PC-FCHIC-01:GRPSTATE'
    BURT_STATUS_PV = 'CS-TI-BL10-01:BURT:OK'
    CYCLING_STATUS_PV = 'CS-TI-BL10-01:STATE'
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

    def __init__(self, parent):
        '''
        Setup UI.
        Connect components and setup all camonitors and associated callbacks.
        '''
        self.knobs = Knobs()

        self.ui = Ui_i10_knobs()
        self.ui.setupUi(parent)
        self.parent = parent

        self.setup_table()

        self.ui.hbpm1_plus_button.clicked.connect(self.hbpm1_plus)
        self.ui.hbpm1_minus_button.clicked.connect(self.hbpm1_minus)
        self.ui.hbpm2_plus_button.clicked.connect(self.hbpm2_plus)
        self.ui.hbpm2_minus_button.clicked.connect(self.hbpm2_minus)
        self.ui.vbpm1_plus_button.clicked.connect(self.vbpm1_plus)
        self.ui.vbpm1_minus_button.clicked.connect(self.vbpm1_minus)
        self.ui.vbpm2_plus_button.clicked.connect(self.vbpm2_plus)
        self.ui.vbpm2_minus_button.clicked.connect(self.vbpm2_minus)
        self.ui.k3_plus_button.clicked.connect(self.k3_plus)
        self.ui.k3_minus_button.clicked.connect(self.k3_minus)
        self.ui.scale_plus_button.clicked.connect(self.scale_plus)
        self.ui.scale_minus_button.clicked.connect(self.scale_minus)
        self.ui.bump_left_plus_button.clicked.connect(self.bump1_plus)
        self.ui.bump_left_minus_button.clicked.connect(self.bump1_minus)
        self.ui.bump_right_plus_button.clicked.connect(self.bump2_plus)
        self.ui.bump_right_minus_button.clicked.connect(self.bump2_minus)

        self.ui.reenable_checkbox.clicked.connect(self.toggle_forbidden_buttons)
        self.ui.small_correction_radiobutton.clicked.connect(lambda: self.set_jog_scaling(0.1))
        self.ui.full_correcton_radiobutton.clicked.connect(lambda: self.set_jog_scaling(1.0))

        camonitor(self.BURT_STATUS_PV, self.update_burt_led)
        camonitor(self.MAGNET_STATUS_PV,
                self.update_magnet_led, format=FORMAT_CTRL)
        camonitor(self.CYCLING_STATUS_PV,
                self.update_cycling_textbox, format=FORMAT_CTRL)

        self.ui.graph = i10plots.Plot()
        self.ui.graph_layout.addWidget(self.ui.graph)
        self.ui.graph.update_colourin()

    def update_cycling_textbox(self, var):
        '''Updates cycling status from enum attached to pv'''
        self.ui.cycling_textbox.setText(QtCore.QString('%s' % var.enums[var]))

    def update_magnet_led(self, var):
        '''Uses PV alarm status to choose color for qframe'''
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, ALARM_COLORS[var.severity])
        self.ui.magnet_led.setPalette(palette)

    def update_burt_led(self, var):
        '''Uses burt valid PV to determine qframe color'''
        palette = QtGui.QPalette()

        # BURT PV is one if okay, zero if bad:
        #    set no alarm (0) or major alarm(2)
        alarm_state = 0 if var==1 else 2

        palette.setColor(QtGui.QPalette.Background, ALARM_COLORS[alarm_state])
        self.ui.burt_led.setPalette(palette)

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
        '''
        Wraps the Knobs.jog method to provide exception handling
        in callbacks.
        '''
        try:
            self.knobs.jog(pvs, ofs)
        except OverCurrentException, e:
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
        '''Change the scaling applied to magnet corrections'''
        self.knobs.jog_scale = scale

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
        max_pvs = [name + ':IMAX' for name in Knobs.NAMES]
        min_pvs = [name + ':IMIN' for name in Knobs.NAMES]
        offset_pvs = [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS]
        seti_pvs = [name + ':SETI' for name in Knobs.NAMES]
        camonitor(max_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.MAX))
        camonitor(min_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.MIN))
        camonitor(offset_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.OFFSET))
        camonitor(seti_pvs,
                lambda x, i: self.update_float(x, i, self.Columns.SETI))

        # Callbacks: Alarm status for each IOC
        alarm_pvs = [name + ':ERRGSTR' for name in Knobs.NAMES]
        camonitor(alarm_pvs,
                lambda x, i: self.update_alarm(x, i, self.Columns.ERRORS),
                format=FORMAT_TIME)

        # Callbacks: High and low values store PVs in a cache for calculations
        self.cache_pvs = (
                [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS] +
                [ctrl + ':WFSCA' for ctrl in Knobs.CTRLS])
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

    def toggle_forbidden_buttons(self):
        '''Switch buttons that may cause beam dumps'''
        enabled = self.ui.reenable_checkbox.isChecked()
        self.ui.scale_plus_button.setEnabled(enabled)
        self.ui.scale_minus_button.setEnabled(enabled)
        self.ui.k3_plus_button.setEnabled(enabled)
        self.ui.k3_minus_button.setEnabled(enabled)
        self.ui.vbpm1_plus_button.setEnabled(enabled)
        self.ui.vbpm1_minus_button.setEnabled(enabled)
        self.ui.vbpm2_plus_button.setEnabled(enabled)
        self.ui.vbpm2_minus_button.setEnabled(enabled)

    def hbpm1_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], self.knobs.left)

    def hbpm1_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], -self.knobs.left)

    def hbpm2_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], self.knobs.right)

    def hbpm2_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], -self.knobs.right)

    def vbpm1_plus(self):
        self.jog_handler([trimname + ':SETI' for trimname in Knobs.TRIMNAMES],
                self.knobs.trimleft)

    def vbpm1_minus(self):
        self.jog_handler([trimname + ':SETI' for trimname in Knobs.TRIMNAMES],
                -self.knobs.trimleft)

    def vbpm2_plus(self):
        self.jog_handler([trimname + ':SETI' for trimname in Knobs.TRIMNAMES],
               self.knobs.trimright)

    def vbpm2_minus(self):
        self.jog_handler([trimname + ':SETI' for trimname in Knobs.TRIMNAMES],
               -self.knobs.trimright)

    def k3_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], self.knobs.dk3)

    def k3_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], -self.knobs.dk3)

    def scale_plus(self):
        self.jog_handler(
               [name + ':SETWFSCA' for name in Knobs.NAMES], self.knobs.dscale)
        self.jog_handler(
               [ctrl + ':WFSCA' for ctrl in Knobs.CTRLS], self.knobs.dscale)

    def scale_minus(self):
        self.jog_handler(
               [name + ':SETWFSCA' for name in Knobs.NAMES], -self.knobs.dscale)
        self.jog_handler(
               [ctrl + ':WFSCA' for ctrl in Knobs.CTRLS], -self.knobs.dscale)

    def bump1_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], self.knobs.b1)

    def bump1_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], -self.knobs.b1)

    def bump2_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], self.knobs.b2)

    def bump2_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in Knobs.CTRLS], -self.knobs.b2)


if __name__ == '__main__':
    # ui business
    cothread.iqt()
    window = QtGui.QMainWindow()
    kui = KnobsUi(window)
    window.show()
    cothread.WaitForQuit()
