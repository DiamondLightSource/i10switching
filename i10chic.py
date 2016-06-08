# matrices.py
# Animated simulation of chicane magnets

# Import libraries

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# Define matrices to modify the electron beam vector:
# drift and kicker magnets.


class Drifting:


    def __init__(self, STEP):
        self.STEP = STEP

    def increment(self, e):
        drift = np.array([[1,self.STEP],
                          [0,1]])
        return np.dot(drift,e)

    def locate(self,where):
        return where + self.STEP

class Kicker:


    def __init__(self, k, STEP):
        self.k = k
        self.STEP = STEP

    def increment(self, e):
        kick = np.array([0, self.k])
        drift = np.array([[1,self.STEP],
                          [0,1]])
        return np.dot(drift,e) + kick

    def locate(self,where):
        return where + self.STEP


# Define the insertion device - needs to be added.

class InsertionDevice:


    def __init__(self, STEP):
        self.STEP = STEP

    def increment(self, e):
        drift = np.array([[1,self.STEP],
                          [0,1]])
        return np.dot(drift,e)

    def locate(self,where):
        return where + self.STEP


# Send electron vector through chicane magnets at time t.

def timestep(t):

    # Initialise electron beam and position within system
    e_beam = np.array([0,0])
    e_pos = [e_beam[0]]
    where = 0
    s = [where]

    # Set size of step through chicane
    STEP = 1

    # Strengths of magnets vary by sin function
    strength = [
        np.sin(t*np.pi/100) + 1, -(1.5)*(np.sin(t*np.pi/100) + 1), 
        1, -(1.5)*(np.sin(t*np.pi/100 + np.pi) + 1), 
        np.sin(t*np.pi/100 + np.pi) + 1
        ]

    path = [
        Drifting(STEP),Kicker(strength[0],STEP),
        Drifting(STEP),Kicker(strength[1],STEP),
        Drifting(STEP),InsertionDevice(STEP),
        Drifting(STEP),Kicker(strength[2],STEP),
        Drifting(STEP),InsertionDevice(STEP),
        Drifting(STEP),Kicker(strength[3],STEP),
        Drifting(STEP),Kicker(strength[4],STEP),
        Drifting(STEP),Drifting(STEP)
        ]

    for p in path:
        e_beam = p.increment(e_beam)
        e_pos.append(e_beam[0])
        where = p.locate(where)
        s.append(where)

    return s, e_pos

# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, 16), ylim=(-2, 5))
line, = ax.plot([], [], lw=2)

# Plot locations of magnets etc
plt.axvline(x=2,color='k',linestyle='dashed')
plt.axvline(x=4,color='k',linestyle='dashed')
plt.axvline(x=8,color='k',linestyle='dashed')
plt.axvline(x=12,color='k',linestyle='dashed')
plt.axvline(x=14,color='k',linestyle='dashed')
plt.plot((6,6), (0, 0), 'r.')
plt.plot((10,10), (0, 0), 'r.')

# Initialisation function: plot the background of each frame.
def init():
    line.set_data([], [])
    return line,

# Animation function
def animate(t):
#    y = timestep(t)
#    x = np.arange(len(y))  # currently just plotting position of electron beam against integers - to be modified
    x = timestep(t)[0]
    y = timestep(t)[1]
    line.set_data(x, y)
    return line,

# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

plt.show()





