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

    def type(self):
        return 'drift'

class Kicker:


    def __init__(self, which):
        self.which = which

    def increment(self, e):
        kick = np.array([0, self.which])
        return e + kick

    def locate(self,where):
        return where

    def type(self):
        return 'kicker'


# Define the insertion device - needs to be added.

class InsertionDevice:


    def __init__(self):
        pass

    def increment(self, e):
        return e

    def locate(self,where):
        return where

    def type(self):
        return 'id'

# Send electron vector through chicane magnets at time t.

def timestep(t):

    # Initialise electron beam and position within system
    e_beam = np.array([0,0])
    e_pos = [e_beam[0]]
    where = 0
    s = [where]
    # Initialise photon beam and position within system
    p_beam = []
    sp = []
    # Initialise locations of insertion devices and kickers
    idloc = []
    kickerloc = []


    # Set size of step through chicane
    STEP = 1

    # Strengths of magnets vary by sin function
    st = np.array([1,1.5,1,1.5,1]) # IS THERE A WAY OF MAKING THE CODE CALCULATE THIS BASED ON THE LOCATIONS OF THE MAGNETS, GIVEN THAT IT CURRENTLY DIFFERENTIATES THE MAGNETS BASED ON THEIR STRENGTHS???
    strength = st*np.array([
        np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
        1, -(np.sin(t*np.pi/100 + np.pi) + 1), 
        np.sin(t*np.pi/100 + np.pi) + 1
        ])

    # Define path through the chicane
    path = [
        Drifting(STEP),Drifting(STEP),Kicker(strength[0]),
        Drifting(STEP),Drifting(STEP),Kicker(strength[1]),
        Drifting(STEP),Drifting(STEP),InsertionDevice(),
        Drifting(STEP),Drifting(STEP),Kicker(strength[2]),
        Drifting(STEP),Drifting(STEP),InsertionDevice(),
        Drifting(STEP),Drifting(STEP),Kicker(strength[3]),
        Drifting(STEP),Drifting(STEP),Kicker(strength[4]),
        Drifting(STEP),Drifting(STEP)
        ]

    # Calculate positions of electron beam, photon beam, kickers and insertion devices.
    for p in range(len(path)):
        obj = path[p].type()
        if obj == 'id':
            idloc.append(path[p].locate(where))
        if obj == 'kicker':
            kickerloc.append(path[p].locate(where))
        e_beam = path[p].increment(e_beam)
        e_pos.append(e_beam[0])
        where = path[p].locate(where)
        s.append(where)



        if obj == 'id':
            p_beam.append(e_beam[0])
            sp.append(where)
        if path[p-1].type() == 'id':
            p_beam.append(e_beam[0])
            sp.append(where)
        if path[p-2].type() == 'id':
            p_beam.append(e_beam[0])
            sp.append(where)



    # Photon beam plotting stuff
    px1 = sp[:len(sp)/2]
    py1 = p_beam[:len(p_beam)/2]
    px2 = sp[len(sp)/2:]
    py2 = p_beam[len(p_beam)/2:]
    
    grad1 = (py1[2]-py1[0])/(px1[2]-px1[0])
    grad2 = (py2[2]-py2[0])/(px2[2]-px2[0])
    for p in np.arange(2,10):
        px1.append(px1[p]+1)
        py1.append(grad1*(px1[p+1]-px1[p])+py1[p])
        px2.append(px2[p]+1)
        py2.append(grad2*(px2[p+1]-px2[p])+py2[p])



    return s, e_pos, idloc, kickerloc, px1, py1, px2, py2


# Attempt to get lines from 3 p_beam points
'''
px = timestep(t)[4]
px1 = px[:len(px)/2]
px2 = px[len(px)/2:]
py = timestep(1)[5]
py1 = py[:len(py)/2]
py2 = py[len(py)/2:]

grad1 = (py1[2]-py1[0])/(px1[2]-px1[0])
px1.append(px1[2]+1)
py1.append(grad1*(px1[3]-px1[2])+py1[2])

plt.plot(px1,py1)
'''












# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, 16), ylim=(-2, 5))
e_line, = ax.plot([], [], lw=1)
idwhere, = ax.plot([], [], 'r.')
p_line, = ax.plot([], [], 'r-')
p_line2, = ax.plot([], [], 'r-')

# Initialisation function: plot the background of each frame.
def init():

    e_line.set_data([], [])
    idwhere.set_data([], [])
    p_line.set_data([],[])
    p_line2.set_data([],[])
    return e_line, idwhere, p_line, p_line2,

import gc  # This can't stay here!
# Animation function
def animate(t):
    data = timestep(t)
    e_line.set_data(data[0], data[1])
    idwhere.set_data(data[2], [0,0])
    k1 = plt.axvline(x=data[3][0], color='k', linestyle='dashed')
    k2 = plt.axvline(x=data[3][1], color='k', linestyle='dashed')
    k3 = plt.axvline(x=data[3][2], color='k', linestyle='dashed')
    k4 = plt.axvline(x=data[3][3], color='k', linestyle='dashed')
    k5 = plt.axvline(x=data[3][4], color='k', linestyle='dashed') # Must be a nicer way...
    p_line.set_data(data[4], data[5])
    p_line2.set_data(data[6], data[7])

    k = [k1, k2, k3, k4, k5]
    gc.collect(0)
    return e_line, idwhere, k1, k2, k3, k4, k5, p_line, p_line2,

# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

plt.show()





