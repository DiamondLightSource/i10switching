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

# Generating clean data
x1 = np.linspace(0, 10, 100)
y1 = gaussian(x1, 1, 5, 2)

x2 = np.linspace(11, 80, 700)
y2 = gaussian(x2, 0.5, 50, 4)

x = np.concatenate([x1,x2])
y = np.concatenate([y1,y2])

# Adding noise to the data
yn = y + 0.1 * np.random.normal(size=len(x))


# Plot out the current state of the data and model
fig = plt.figure()
ax1 = fig.add_subplot(211)
scatterplot = ax1.plot(x,y,'.')[0]
scatterplot.set_ydata(yn)


ax2 = fig.add_subplot(212)

subset = [ax2.plot(x[:100],y[:100],'b.')[0], ax2.plot(x[:200],y[400:600],'r.')[0]]  # need to deal with different width issues when overlaying
subset[0].set_ydata(yn[:100])
subset[1].set_ydata(yn[400:600])



plt.show()
