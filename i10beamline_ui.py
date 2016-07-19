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
from cothread.catools import caput, camonitor, FORMAT_TIME

import os
import traceback

from PyQt4 import QtGui
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
    I10_ADC_3_PV = 'BL10I-EA-USER-01:WAI3'

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

        self.ui.bump_left_plus_button.clicked.connect(self.bump1_plus)
        self.ui.bump_left_minus_button.clicked.connect(self.bump1_minus)
        self.ui.bump_right_plus_button.clicked.connect(self.bump2_plus)
        self.ui.bump_right_minus_button.clicked.connect(self.bump2_minus)

        self.ui.small_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(0.1))
        self.ui.full_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(1.0))

        self.ui.traces = i10plots.Traces(self.I10_ADC_1_PV, self.I10_ADC_2_PV)
        self.ui.graph = i10plots.OverlaidWaveforms(
                                        self.I10_ADC_1_PV, self.I10_ADC_2_PV)

        self.ui.graph_layout.addWidget(self.ui.traces)
        self.ui.graph_layout.addWidget(self.ui.graph)
        self.ui.checkBox.clicked.connect(self.gauss_fit)

    def gauss_fit(self):
        if self.ui.checkBox.isChecked() == True:
            self.ui.graph.gaussian(2.5, 900) # make this adjustable
        else:
            self.ui.graph.clear_gaussian()

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
        self.knobs.jog_scale = scale

    def bump1_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in self.knobs.CTRLS], self.knobs.b1)

    def bump1_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in self.knobs.CTRLS], -self.knobs.b1)

    def bump2_plus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in self.knobs.CTRLS], self.knobs.b2)

    def bump2_minus(self):
        self.jog_handler(
               [ctrl + ':OFFSET' for ctrl in self.knobs.CTRLS], -self.knobs.b2)


if __name__ == '__main__':
    # ui business
    cothread.iqt()
    kui = KnobsUi()
    kui.ui.show()
    cothread.WaitForQuit()

