#!/usr/bin/env dls-python2.7

# i10knobs simplified to see what it's like without the table...

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

import cothread
from cothread.catools import caget, caput, camonitor, FORMAT_TIME, FORMAT_CTRL
import numpy
import scipy.io
import os, sys
import traceback

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

import i10plots


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


class KnobsUi(QtGui.QMainWindow):

    '''
    Provides the GUI to the underlying Knobs class.
    Relevant status information is also gathered from PVs
    and shown to the user.
    '''

    UI_FILENAME = 'i10beamlineui.ui'
    I10_ADC_1_PV = 'BL10I-EA-USER-01:WAI1'
    I10_ADC_2_PV = 'BL10I-EA-USER-01:WAI2'
    I10_ADC_3_PV = 'BL10I-EA-USER-01:WAI3'

    HIGHLIGHT_COLOR = QtGui.QColor(235, 235, 235) # Light grey

    def __init__(self):
        '''
        Setup UI.
        Connect components and setup all camonitors and associated callbacks.
        '''
        self.knobs = Knobs()
        QtGui.QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), self.UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.parent = QtGui.QMainWindow()

        self.ui.bump_left_plus_button.clicked.connect(self.bump1_plus)
        self.ui.bump_left_minus_button.clicked.connect(self.bump1_minus)
        self.ui.bump_right_plus_button.clicked.connect(self.bump2_plus)
        self.ui.bump_right_minus_button.clicked.connect(self.bump2_minus)

        self.ui.small_correction_radiobutton.clicked.connect(lambda: self.set_jog_scaling(0.1))
        self.ui.full_correcton_radiobutton.clicked.connect(lambda: self.set_jog_scaling(1.0))

        self.ui.trig = i10plots.Trigger()
        self.ui.graph = i10plots.WaveformCanvas(self.I10_ADC_1_PV, self.I10_ADC_2_PV)

        self.ui.graph_layout.addWidget(self.ui.trig)
        self.ui.graph_layout.addWidget(self.ui.graph)

        self.ui.trig.plot_trigger(self.I10_ADC_1_PV)

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
    kui = KnobsUi()
    kui.ui.show()
    cothread.WaitForQuit()

