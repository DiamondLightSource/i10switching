#i10controls.py

#import cothread
from cothread.catools import *

class ARRAYS(object):
    OFFSETS = 'offsets'
    SCALES = 'scales'

CTRLS = [
    'SR09A-PC-CTRL-01',
    'SR09A-PC-CTRL-02',
    'SR10S-PC-CTRL-03',
    'SR10S-PC-CTRL-04',
    'SR10S-PC-CTRL-05']

arrays = {'offsets': caget([ctrl + ':OFFSET' for ctrl in CTRLS]), 'scales': caget([ctrl + ':WFSCA' for ctrl in CTRLS])}

listeners = []

def register_listener(l):
    listeners.append(l)

def update_mag_values(val, key, index):
    arrays[key][index] = val # this updates arrays
    [l(key, index) for l in listeners] # this tells listener which value has changed

for i in range(len(CTRLS)):
    camonitor(CTRLS[i] + ':OFFSET', lambda x: update_mag_values(x, 'offsets', i))
    camonitor(CTRLS[i] + ':WFSCA', lambda x: update_mag_values(x, 'scales', i))

# need to work out how scale buttons update
