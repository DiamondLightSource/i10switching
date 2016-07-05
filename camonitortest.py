import dls_packages
import cothread
import numpy as np
from cothread.catools import *
import matplotlib.pyplot as plt

plt.plot(caget('BL10I-EA-USER-01:WAI1'), 'r')
#plt.draw()
plt.show()

def update_plot(value):
    print 'test'

#    lines[0].set_ydata(value)
#    plt.draw()

    plt.plot(value)
    plt.draw()

def printout(value):
    print value

camonitor('BL10I-EA-USER-01:WAI1', printout)
plt.show(block=False)
cothread.WaitForQuit()

#### I GIVE UP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
