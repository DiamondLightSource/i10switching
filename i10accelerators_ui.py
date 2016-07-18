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
from PyQt4.QtGui import QMainWindow
import os

import i10plots
import i10buttons

###########################
########### GUI ###########
###########################


class Gui(QMainWindow):

    UI_FILENAME = 'i10chicgui.ui'

    I10_ADC_1_PV = 'BL10I-EA-USER-01:WAI1'
    I10_ADC_2_PV = 'BL10I-EA-USER-01:WAI2'
    I10_ADC_3_PV = 'BL10I-EA-USER-01:WAI3'

    def __init__(self):
        QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), self.UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.parent = QtGui.QMainWindow()

        self.ui.simulation = i10plots.Plot()
        self.ui.displaytrace = i10plots.WaveformCanvas(
                               self.I10_ADC_1_PV, self.I10_ADC_2_PV)
        self.ui.gaussians = i10plots.GaussPlot()
        self.ui.trig = i10plots.Trigger()
        self.toolbar = NavigationToolbar(self.ui.gaussians, self)
        self.knobs = i10buttons.Knobs()

        self.ui.graphLayout.addWidget(self.ui.simulation) # do I want tabs? if not go back to matplotlib_layout and just delete the tab thing in pyqt
        self.ui.graphLayout.addWidget(self.ui.trig)
        self.ui.graphLayout.addWidget(self.ui.displaytrace)
        self.ui.graphLayout2.addWidget(self.ui.gaussians)
        self.ui.graphLayout.addWidget(self.toolbar)

        self.ui.kplusButton.clicked.connect(lambda: self.btn_ctrls(1, 0))
        self.ui.kminusButton.clicked.connect(lambda: self.btn_ctrls(-1, 0))

        self.ui.bumpleftplusButton.clicked.connect(lambda: self.btn_ctrls(1, 1))
        self.ui.bumpleftplusButton.clicked.connect(self.bump1_plus)

        self.ui.bumpleftminusButton.clicked.connect(lambda: self.btn_ctrls(-1, 1))
        self.ui.bumpleftminusButton.clicked.connect(self.bump1_minus)

        self.ui.bumprightplusButton.clicked.connect(lambda: self.btn_ctrls(1, 2))
        self.ui.bumprightplusButton.clicked.connect(self.bump2_plus)

        self.ui.bumprightminusButton.clicked.connect(lambda: self.btn_ctrls(-1, 2))
        self.ui.bumprightminusButton.clicked.connect(self.bump2_minus)

        self.ui.bpm1plusButton.clicked.connect(lambda: self.btn_ctrls(1, 3))
        self.ui.bpm1minusButton.clicked.connect(lambda: self.btn_ctrls(-1, 3))
        self.ui.bpm2plusButton.clicked.connect(lambda: self.btn_ctrls(1, 4))
        self.ui.bpm2minusButton.clicked.connect(lambda: self.btn_ctrls(-1, 4))
        self.ui.scaleplusButton.clicked.connect(lambda: self.btn_ctrls(1, 5))
        self.ui.scaleminusButton.clicked.connect(lambda: self.btn_ctrls(-1, 5))
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.simulation.update_colourin()
        self.ui.gaussians.display()
        self.ui.trig.plot_trigger(self.I10_ADC_1_PV)

    def btn_ctrls(self, factor, which_button):
        self.ui.simulation.info.magnets.buttons(factor, which_button)
        self.ui.simulation.ax.collections.remove(self.ui.simulation.fill1)
        self.ui.simulation.ax.collections.remove(self.ui.simulation.fill2)
        self.ui.simulation.update_colourin()

    def reset(self):
        self.ui.simulation.info.magnets.reset()
        self.ui.simulation.ax.collections.remove(self.ui.simulation.fill1)
        self.ui.simulation.ax.collections.remove(self.ui.simulation.fill2)
        self.ui.simulation.update_colourin()

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

def main():
    cothread.iqt()
    the_ui = Gui()
    the_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()


