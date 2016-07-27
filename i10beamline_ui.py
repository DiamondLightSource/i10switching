#!/usr/bin/env dls-python2.7
# i10beamline_ui.py
# Gui linking to i10plots, straight, buttons
# Contains KnobsUi

"""
Buttons to move I10 fast chicane magnet offsets and scales.
Provides a gui to control magnet scaling and offsets in order
to allow independant steering of photon and electron beams to
maintain a closed bump. Displays the two x-ray peaks such that
they overlap and calculates the area of each to indicate their
relative intensities.
"""

from pkg_resources import require
require('numpy==1.11.1')
require('scipy==0.10.1')
require('matplotlib==1.3.1')
require('cothread==2.13')

import cothread
from cothread.catools import caput, camonitor, FORMAT_TIME, FORMAT_CTRL

import os
import traceback

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic
from PyQt4.QtGui import QMainWindow

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

class KnobsUi(QMainWindow):
    """
    GUI containing buttons to control the beam and displaying the
    trigger and x-ray waveform traces. The two peaks of the x-ray
    waveform are displayed overlapped with their areas calculated.
    """

    UI_FILENAME = 'i10beamlineui.ui'

    HIGHLIGHT_COLOR = QtGui.QColor(235, 235, 235) # Light grey

    def __init__(self):

        QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), self.UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.parent = QtGui.QMainWindow()

        self.straight = i10straight.Straight()
        self.knobs = i10buttons.MagnetCoordinator()

        """
        Initialise amplitude and standard deviation of theoretical
        gaussian.
        """
        self.amp = 2.5
        self.sig = 900

        self.traces = i10plots.Traces(self.straight.controls)
        self.graph = i10plots.OverlaidWaveforms(self.straight.controls)

        """Connect buttons to PVs."""
        self.ui.bump_left_plus_button.clicked.connect(self.bump1_plus)
        self.ui.bump_left_minus_button.clicked.connect(self.bump1_minus)
        self.ui.bump_right_plus_button.clicked.connect(self.bump2_plus)
        self.ui.bump_right_minus_button.clicked.connect(self.bump2_minus)

        self.ui.ampplusButton.clicked.connect(self.amp_plus)
        self.ui.ampminusButton.clicked.connect(self.amp_minus)
        self.ui.sigmaplusButton.clicked.connect(self.sig_plus)
        self.ui.sigmaminusButton.clicked.connect(self.sig_minus)
        self.ui.ampplusButton.setEnabled(False)
        self.ui.ampminusButton.setEnabled(False)
        self.ui.sigmaplusButton.setEnabled(False)
        self.ui.sigmaminusButton.setEnabled(False)

        self.ui.checkBox.clicked.connect(self.gauss_fit)

        self.ui.small_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(0.1))
        self.ui.full_correction_radiobutton.clicked.connect(
                                        lambda: self.set_jog_scaling(1.0))

        """Monitor the states of magnets and cycling."""
        camonitor(i10buttons.MagnetCoordinator.MAGNET_STATUS_PV,
                  self.update_magnet_led, format=FORMAT_CTRL)
        camonitor(i10buttons.MagnetCoordinator.CYCLING_STATUS_PV,
                  self.update_cycling_textbox, format=FORMAT_CTRL)

        """Add graphs to the GUI."""
        self.ui.graph_layout.addWidget(self.traces)
        self.ui.graph_layout.addWidget(self.graph)

    def gauss_fit(self):
        
        """Overlay theoretical gaussian and enable buttons to modify it."""

        enabled = self.ui.checkBox.isChecked()
        self.ui.ampplusButton.setEnabled(enabled)
        self.ui.ampminusButton.setEnabled(enabled)
        self.ui.sigmaplusButton.setEnabled(enabled)
        self.ui.sigmaminusButton.setEnabled(enabled)
        if enabled == True:
            self.graph.gaussian(self.amp, self.sig)
        else:
            self.graph.clear_gaussian()


    """Methods controlling the theoretical gaussian."""

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

    def jog_handler(self, pvs, old_values, ofs, factor):

        """
        Wrap the MagnetCoordinator.jog method to provide exception handling
        in callbacks; updates PVs.
        """

        try:
            jog_pvs = self.knobs.jog(pvs, old_values, ofs, factor)
            self.straight.controls.set_new_pvs(jog_pvs[0], jog_pvs[1])
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
        self.knobs.jog_scale = scale

    """Methods linking buttons to offset/scale values for adjusting PVs."""

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

    def update_cycling_textbox(self, var):
        """Updates cycling status from enum attached to pv"""
        self.ui.cycling_textbox_3.setText(QtCore.QString('%s' % var.enums[var]))

    def update_magnet_led(self, var):
        """Uses PV alarm status to choose color for qframe"""
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, i10buttons.ALARM_COLORS[var.severity])
        self.ui.magnet_led_3.setPalette(palette)


if __name__ == '__main__':
    # ui business
    cothread.iqt()
    kui = KnobsUi()
    kui.ui.show()
    cothread.WaitForQuit()

