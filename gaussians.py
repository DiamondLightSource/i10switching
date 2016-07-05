# plots a fake pair of gaussians (and overlays them hopefully)
import dls_packages
#import numpy as np
#import matplotlib.pyplot as plt

import numpy as np
#from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Let's create a function to model and create data
def gaussian(x, a, x0, sigma):
    return a*np.exp(-(x-x0)**2/(2*sigma**2))

# Generate square wave trigger
xsq = [0,20,80,100]
ysq = [0,0,1,0]

# Generating clean data
x = np.linspace(0, 100, 1000)
y1 = gaussian(x[:500], 1, xsq[1]+1, 2)
y2 = gaussian(x[500:], 0.5, xsq[2]+1, 4)


y = np.concatenate([y1,y2])

# Adding noise to the data
yn = y + 0.02 * np.random.normal(size=len(x))


# Plot out the current state of the data and model
fig = plt.figure()
ax1 = fig.add_subplot(311)
scatterplot = [ax1.plot(x,y)[0], ax1.step(xsq,ysq)[0]]
scatterplot[0].set_ydata(yn)
plt.ylim(-0.1,1.2)


ax2 = fig.add_subplot(312)

#subset = [ax2.plot(np.linspace(-5,5,100),y[:100],'b')[0], ax2.plot(np.linspace(-10,10,200),y[450:650],'r')[0]]  # need to deal with different width issues when overlaying
#subset[0].set_ydata(yn[:100])
#subset[1].set_ydata(yn[450:650])

ax3 = fig.add_subplot(313)

for i in range(len(yn)):
    if yn[i] > 0.1 and x[i] < x[len(x)/2]:
        print i


plt.show()
