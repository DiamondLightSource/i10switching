# overlays gaussians

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as integ


# Import data
trigger = np.load('trigger.npy')[1200:6200]
trace = np.load('diode.npy')[1200:6200]

# Number of data points
GRAPHRANGE = 5000
WINDOW = GRAPHRANGE/2
# Shift between edge of square wave and peak of Gaussian
CENTRESHIFT = 25

x = np.linspace(0, GRAPHRANGE, GRAPHRANGE)

# Finds edges of square wave
sqdiff = np.diff(trigger).tolist()
edges = [sqdiff.index(max(sqdiff)), sqdiff.index(min(sqdiff))]

# Plot out the current state of the data and model
fig = plt.figure()
ax1 = fig.add_subplot(211)
ax1.plot(x,trigger)
ax1.plot(x,trace)

# Overlay the two gaussians
ax2 = fig.add_subplot(212)
peak1 = np.array(trace[:WINDOW])
peak2 = np.array(trace[WINDOW:])
xwindow = np.linspace(-WINDOW/2, WINDOW/2, WINDOW)
peak1shift = WINDOW/2 - edges[0] - CENTRESHIFT
peak2shift = 3*WINDOW/2 - edges[1] - CENTRESHIFT
ax2.plot(xwindow + peak1shift,peak1, label=integ.simps(peak1))
ax2.plot(xwindow + peak2shift,peak2, label=integ.simps(peak2))
ax2.legend()

plt.show()

