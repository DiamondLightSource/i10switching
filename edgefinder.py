import dls_packages
import matplotlib.pyplot as plt
import numpy as np

trigger = np.load('trigger.npy')
plt.plot(trigger)


diff = np.diff(trigger).tolist()

try:
    maxt = next(x for x in diff if x > 0.1)
    print maxt, diff.index(maxt)

    try:
        mint = next(x for x in diff[diff.index(maxt):] if x < -0.1)
        print mint, diff.index(mint)
    except StopIteration:
        print 'Incomplete trace'

except StopIteration:
    print 'Incomplete trace'

plt.show()
