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


    def __init__(self,STEP):
        self.STEP = STEP

    def increment(self, e):
        drift = np.array([[1,self.STEP],
                          [0,1]])
        return np.dot(drift,e)


class Kicker:


    def __init__(self,k,STEP):
        self.k = k
        self.STEP = STEP

    def increment(self, e):
        kick = np.array([0, self.k])
        drift = np.array([[1,self.STEP],
                          [0,1]])
        return np.dot(drift,e) + kick

#    def locate(self):
#        return ???


# Define the insertion device - needs to be added.


class InsertionDevice:


    def __init__(self,e):
        self.e = e

#    def where(self):
#        return ???


# Send electron vector through chicane magnets at time t.

def timestep(t):

    # Initialise electron beam and position within system
    e_beam = np.array([0,0])
    e_pos = [e_beam[0]]
#    s = 0

    # Set size of step through chicane
    STEP = 1

    # Strengths of magnets vary by sin function
    strength = [
        np.sin(t*np.pi/100) + 1, -(1.5)*(np.sin(t*np.pi/100) + 1), 
        1, -(1.5)*(np.sin(t*np.pi/100 + np.pi) + 1), 
        np.sin(t*np.pi/100 + np.pi) + 1
        ]



    path = [Drifting(STEP),Kicker(strength[0],STEP),Drifting(STEP),Kicker(strength[1],STEP),Drifting(STEP),Drifting(STEP),Drifting(STEP),Kicker(strength[2],STEP),Drifting(STEP),Drifting(STEP),Drifting(STEP),Kicker(strength[3],STEP),Drifting(STEP),Kicker(strength[4],STEP),Drifting(STEP),Drifting(STEP)]

    for p in path:
        e_beam = p.increment(e_beam)
        e_pos.append(e_beam[0])

    '''
    # Path of electron beam through chicane magnets:
    # Drift
    e_beam = Drifting(STEP,e_beam).increment() #want to increase s by STEP each time # maybe have an overall class that you can call to increment s, apply drift or kicker, add on position...
    e_pos.append(e_beam[0])
    # First kicker
    e_beam = Drifting(STEP,e_beam).increment()
    e_beam = Kicker(strength[0],e_beam).dipole()
    e_pos.append(e_beam[0])
    # Drift
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])
    # Second kicker
    e_beam = Drifting(STEP,e_beam).increment()
    e_beam = Kicker(strength[1],e_beam).dipole()
    e_pos.append(e_beam[0])
    # Drift
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])  # insertion device here - to be added later
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])
    # Third kicker
    e_beam = Drifting(STEP,e_beam).increment()
    e_beam = Kicker(strength[2],e_beam).dipole()
    e_pos.append(e_beam[0])
    # Drift
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])  	# insertion device here - to be added later
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])
    # Fourth kicker
    e_beam = Drifting(STEP,e_beam).increment()
    e_beam = Kicker(strength[3],e_beam).dipole()
    e_pos.append(e_beam[0])
    # Drift
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])
    # Fifth kicker
    e_beam = Drifting(STEP,e_beam).increment()
    e_beam = Kicker(strength[4],e_beam).dipole()
    e_pos.append(e_beam[0])
    # Drift
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])
    e_beam = Drifting(STEP,e_beam).increment()
    e_pos.append(e_beam[0])
    '''
    return e_pos

# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, 16), ylim=(-2, 5))
line, = ax.plot([], [], lw=2)

# Initialization function: plot the background of each frame.
def init():
    line.set_data([], [])
    return line,

# Animation function
def animate(t):
    y = timestep(t)
    x = np.arange(len(y))  # currently just plotting position of electron beam against integers - to be modified
    line.set_data(x, y)
    return line,

# Call the animator.
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

plt.show()





