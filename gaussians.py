# plots a fake pair of gaussians (and overlays them hopefully)
import dls_packages
import numpy as np
import matplotlib.pyplot as plt

# Let's create a function to model and create data
def gaussian(x, a, x0, sigma):
    return a*np.exp(-(x-x0)**2/(2*sigma**2))

GRAPHRANGE = 100
GRAPHSCALE = 10
CENTRESHIFT = 1
WINDOW = 10

# Generate square wave trigger
xsq = [0,20,80,GRAPHRANGE]
ysq = [0,0,1,0]

# Generating clean data
x = np.linspace(0, GRAPHRANGE, GRAPHRANGE*GRAPHSCALE)
y1 = gaussian(x[:GRAPHRANGE*GRAPHSCALE/2], 1, xsq[1]+CENTRESHIFT, 2)
y2 = gaussian(x[GRAPHRANGE*GRAPHSCALE/2:], 0.5, xsq[2]+CENTRESHIFT, 4)
y = np.concatenate([y1,y2])

# Adding noise to the data
yn = y + 0.02 * np.random.normal(size=len(x))

# Plot out the current state of the data and model
fig = plt.figure()
ax1 = fig.add_subplot(311)
scatterplot = [ax1.plot(x,y)[0], ax1.step(xsq,ysq)[0]]
scatterplot[0].set_ydata(yn)
plt.ylim(-0.1,1.2)

# Overlay the two gaussians
ax2 = fig.add_subplot(312)
subset1 = np.array(yn[GRAPHSCALE * (xsq[1] - WINDOW + CENTRESHIFT) : GRAPHSCALE * (xsq[1] + WINDOW + CENTRESHIFT)])
subset2 = np.array(yn[GRAPHSCALE * (xsq[2] - WINDOW + CENTRESHIFT) : GRAPHSCALE * (xsq[2] + WINDOW + CENTRESHIFT)])
x = np.linspace(0, len(subset1)/GRAPHSCALE, len(subset1))
ax2.plot(x,subset1)
ax2.plot(x,subset2)

ax3 = fig.add_subplot(313)


plt.show()
