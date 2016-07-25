#i10controls.py

import cothread
from cothread.catools import *


class Controls(object):

    CTRLS = [
        'SR09A-PC-CTRL-01',
        'SR09A-PC-CTRL-02',
        'SR10S-PC-CTRL-03',
        'SR10S-PC-CTRL-04',
        'SR10S-PC-CTRL-05']

    TRACES = [
        'BL10I-EA-USER-01:WAI1',
        'BL10I-EA-USER-01:WAI2']


    class ARRAYS(object):
        OFFSETS = 'offsets'
        SCALES = 'scales'
        WAVEFORMS = 'waveforms'

    def __init__(self):
        self.arrays = {'offsets': caget([ctrl + ':OFFSET' for ctrl in self.CTRLS]), 'scales': caget([ctrl + ':WFSCA' for ctrl in self.CTRLS]), 'waveforms': caget(self.TRACES)}
        self.listeners = []
        for i in range(len(self.CTRLS)):
            camonitor(self.CTRLS[i] + ':OFFSET', lambda x, i=i: self.update_values(x, 'offsets', i))
            camonitor(self.CTRLS[i] + ':WFSCA', lambda x, i=i: self.update_values(x, 'scales', i))
        for i in range(len(self.TRACES)):
            camonitor(self.TRACES[i], lambda x, i=i: self.update_values(x, 'waveforms', i))

    def register_listener(self, l):
        self.listeners.append(l)

    def update_values(self, val, key, index):
        self.arrays[key][index] = val # this updates arrays
        [l(key, index) for l in self.listeners] # this tells listener which value has changed










# need to sort out how scale buttons update in simulation



#for i in range(len(TRACES)):
#    camonitor(TRACES[i], lambda x: update_values(x, 'traces', i))


