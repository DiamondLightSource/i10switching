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
import i10controls
import writers


# Alarm colours
ALARM_COLORS = [
        QtGui.QColor(0, 215, 20), # None
        QtGui.QColor(255, 140, 0), # Minor
        QtGui.QColor(255, 0, 0), # Major
        QtGui.QColor(255, 0, 255), # Invalid
        ]


class KnobsUi(QMainWindow):

    """
    GUI for the beamline users.

    GUI containing buttons to control the beam and displaying the
    trigger and x-ray waveform traces. The two peaks of the x-ray
    waveform are displayed overlapped with their areas calculated.
    """

    UI_FILENAME = 'i10beamlineui.ui'

    def __init__(self):

        QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), self.UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.parent = QtGui.QMainWindow()

        self.pv_monitor = i10controls.PvMonitors.get_instance()
        self.knobs = i10buttons.MagnetCoordinator()
        self.pv_writer = writers.PvWriter()

        """Initial setting for GUI: jog scaling = 1."""
        self.jog_scale = 1.0

        """Initialise amplitude and standard deviation of gaussian."""
        self.amp = 2.5
        self.sig = 900

        self.traces = i10plots.Traces(i10controls)
        self.graph = i10plots.OverlaidWaveforms(i10controls)

        """Connect buttons to PVs."""
        self.ui.bumpleftplusButton.clicked.connect(
                lambda: self.jog_handler(i10buttons.Moves.BUMP_LEFT, 1))
        self.ui.bumpleftminusButton.clicked.connect(
                lambda: self.jog_handler(i10buttons.Moves.BUMP_LEFT, -1))
        self.ui.bumprightplusButton.clicked.connect(
                lambda: self.jog_handler(i10buttons.Moves.BUMP_RIGHT, 1))
        self.ui.bumprightminusButton.clicked.connect(
                lambda: self.jog_handler(i10buttons.Moves.BUMP_RIGHT, -1))

        self.ui.ampplusButton.clicked.connect(self.amp_plus)
        self.ui.ampminusButton.clicked.connect(self.amp_minus)
        self.ui.sigmaplusButton.clicked.connect(self.sig_plus)
        self.ui.sigmaminusButton.clicked.connect(self.sig_minus)
        self.ui.ampplusButton.setEnabled(False)
        self.ui.ampminusButton.setEnabled(False)
        self.ui.sigmaplusButton.setEnabled(False)
        self.ui.sigmaminusButton.setEnabled(False)

        self.ui.checkBox.clicked.connect(self.gauss_fit)

        self.ui.jog_scale_slider.valueChanged.connect(self.set_jog_scaling)
        self.ui.jog_scale_textbox.setText(str(self.jog_scale))

        """Monitor the states of magnets and cycling."""
        camonitor(i10controls.PvReferences.MAGNET_STATUS_PV,
                  self.update_magnet_led, format=FORMAT_CTRL)
        camonitor(i10controls.PvReferences.CYCLING_STATUS_PV,
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
        if enabled:
            self.graph.gaussian(self.amp, self.sig)
        else:
            self.graph.clear_gaussian()

    def set_jog_scaling(self):
        """Change the scaling applied to magnet corrections."""
        self.jog_scale = self.ui.jog_scale_slider.value() * 0.1
        self.ui.jog_scale_textbox.setText(str(self.jog_scale))

    """Methods controlling the theoretical gaussian."""

    def amp_plus(self):
        self.amp += 0.1
        self.graph.clear_gaussian()
        self.graph.gaussian(self.amp, self.sig)

    def amp_minus(self):
        self.amp -= 0.1
        self.graph.clear_gaussian()
        self.graph.gaussian(self.amp, self.sig)

    def sig_plus(self):
        self.sig += 10
        self.graph.clear_gaussian()
        self.graph.gaussian(self.amp, self.sig)

    def sig_minus(self):
        self.sig -= 10
        self.graph.clear_gaussian()
        self.graph.gaussian(self.amp, self.sig)

    def jog_handler(self, key, factor):

        """
        Handle button clicks.

        When button clicked this class sends information to the writer and
        provides exception handling in callbacks.
        """

        try:
            self.pv_writer.write(key, factor, self.jog_scale)
            self.update_shading()

        except i10buttons.OverCurrentException, e:
            msgBox = QtGui.QMessageBox(self.parent)
            msgBox.setText('OverCurrent Exception: current applied to magnet %s is too high.' % e.magnet_index)
            msgBox.exec_()
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

    def update_cycling_textbox(self, var):
        """Updates cycling status from enum attached to pv"""
        self.ui.cycling_textbox_3.setText(QtCore.QString('%s' % var.enums[var]))

    def update_magnet_led(self, var):
        """Uses PV alarm status to choose color for qframe"""
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, ALARM_COLORS[var.severity])
        self.ui.magnet_led_3.setPalette(palette)


if __name__ == '__main__':
    # ui business
    cothread.iqt()
    kui = KnobsUi()
    kui.ui.show()
    cothread.WaitForQuit()
