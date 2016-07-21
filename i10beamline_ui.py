#!/usr/bin/env dls-python2.7



"""
Buttons to move I10 fast chicane magnet offsets and scales.

Provides a gui to control magnet scaling and offsets
in order to allow independant steering of photon and
electron beams to maintain a closed bump.
"""

from pkg_resources import require
require('cothread==2.10')
require('scipy==0.10.1')
require('matplotlib==1.3.1')

import cothread
from cothread.catools import caput, camonitor, FORMAT_TIME, FORMAT_CTRL

import os
import traceback

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic

import i10plots
import i10buttons


class KnobsUi(QtGui.QMainWindow):
    """
    Provides the GUI to the underlying Knobs class.
    Relevant status information is also gathered from PVs
    and shown to the user.
    """
    UI_FILENAME = 'i10beamlineui.ui'
    I10_ADC_1_PV = 'BL10I-EA-USER-01:WAI1'
    I10_ADC_2_PV = 'BL10I-EA-USER-01:WAI2'
    I10_ADC_3_PV = 'BL10I-EA-USER-01:WAI3' # unused??

    HIGHLIGHT_COLOR = QtGui.QColor(235, 235, 235) # Light grey

    def __init__(self):
        """
        Setup UI.
        Connect components and setup all camonitors and associated callbacks.
        """
        self.knobs = i10buttons.Knobs()
        QtGui.QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), self.UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.parent = QtGui.QMainWindow()

        self.amp = 2.5
        self.sig = 900

        self.ui.bump_left_plus_button.clicked.connect(self.bump1_plus)
        self.ui.bump_left_minus_button.clicked.connect(self.bump1_minus)
        self.ui.bump_right_plus_button.clicked.connect(self.bump2_plus)
        self.ui.bump_right_minus_button.clicked.connect(self.bump2_minus)
        self.ui.ampplusButton.clicked.connect(self.amp_plus)
        self.ui.ampminusButton.clicked.connect(self.amp_minus)
        self.ui.sigmaplusButton.clicked.connect(self.sig_plus)
        self.ui.sigmaminusButton.clicked.connect(self.sig_minus)
        self.ui.checkBox.clicked.connect(self.gauss_fit)
        self.ui.ampplusButton.setEnabled(False)
        self.ui.ampminusButton.setEnabled(False)
        self.ui.sigmaplusButton.setEnabled(False)
        self.ui.sigmaminusButton.setEnabled(False)
        self.ui.small_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(0.1))
        self.ui.full_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(1.0))

        camonitor(i10buttons.Knobs.MAGNET_STATUS_PV,
                self.update_magnet_led, format=FORMAT_CTRL)
        camonitor(i10buttons.Knobs.CYCLING_STATUS_PV,
                self.update_cycling_textbox, format=FORMAT_CTRL)

        self.traces = i10plots.Traces(self.I10_ADC_1_PV, self.I10_ADC_2_PV)
        self.graph = i10plots.OverlaidWaveforms(
                                        self.I10_ADC_1_PV, self.I10_ADC_2_PV)

        self.ui.graph_layout.addWidget(self.traces)
        self.ui.graph_layout.addWidget(self.graph)

    def gauss_fit(self):
        enabled = self.ui.checkBox.isChecked()
        self.ui.ampplusButton.setEnabled(enabled)
        self.ui.ampminusButton.setEnabled(enabled)
        self.ui.sigmaplusButton.setEnabled(enabled)
        self.ui.sigmaminusButton.setEnabled(enabled)
        if enabled == True:
            self.graph.gaussian(self.amp, self.sig)
        else:
            self.graph.clear_gaussian()

    def amp_plus(self):
        self.amp = self.amp + 0.1
        self.graph.clear_gaussian()
        self.graph.gaussian(self.amp, self.sig)

    def amp_minus(self):
        self.amp = self.amp - 0.1
        self.graph.clear_gaussian()
        self.graph.gaussian(self.amp, self.sig)

    def sig_plus(self):
        self.sig = self.sig + 10
        self.graph.clear_gaussian()
        self.graph.gaussian(self.amp, self.sig)

    def sig_minus(self):
        self.sig = self.sig - 10
        self.graph.clear_gaussian()
        self.graph.gaussian(self.amp, self.sig)

    def jog_handler(self, pvs, ofs):
        """
        Wrap the Knobs.jog method to provide exception handling
        in callbacks.
        """
        try:
            self.knobs.jog(pvs, ofs)
        except i10buttons.OverCurrentException, e:
            self.flash_table_cell(self.Columns.OFFSET, e.magnet_index) # no table in this gui - put something else in to warn?
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
        i10buttons.Knobs.jog_scale = scale

    def bump1_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                self.knobs.button_data['BUMP_LEFT'])

    def bump1_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                -self.knobs.button_data['BUMP_LEFT'])

    def bump2_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                self.knobs.button_data['BUMP_RIGHT'])

    def bump2_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in i10buttons.Knobs.CTRLS],
                -self.knobs.button_data['BUMP_RIGHT'])

    def update_cycling_textbox(self, var):
        '''Updates cycling status from enum attached to pv'''
        self.ui.cycling_textbox_3.setText(QtCore.QString('%s' % var.enums[var]))

    def update_magnet_led(self, var):
        '''Uses PV alarm status to choose color for qframe'''
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, i10buttons.ALARM_COLORS[var.severity])
        self.ui.magnet_led_3.setPalette(palette)


if __name__ == '__main__':
    # ui business
    cothread.iqt()
    kui = KnobsUi()
    kui.ui.show()
    cothread.WaitForQuit()

