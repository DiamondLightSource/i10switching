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


    def __init__(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

    def type(self):
        return 'drift'


class Kicker:


    def __init__(self, k):
        self.k = k

    def increment(self, e):
        kick = np.array([0, self.k])
        return e + kick

    def type(self):
        return 'kicker'


class InsertionDevice:


    def __init__(self):
        pass

    def increment(self, e):
        return e

    def type(self):
        return 'id'


# Define positions of stuff in system
length = [2,2,6,6,6,6,2,2] #lengths to drift between kickers and ids, must be symmetric about centre magnet
p = 0
pos = [p]
for L in length:
    p += L
    pos.append(p)
kicker_pos = [pos[1],pos[2],pos[4],pos[6],pos[7]]
id_pos = [pos[3],pos[5]] #is there a nicer way of doing this?
p1_pos = [pos[3],pos[4]]
p2_pos = [pos[5],pos[6]]
p_pos = [pos[3],pos[4],pos[5],pos[6]]
for i in np.arange(2,10):
    p1_pos.append(pos[4]+i)
    p2_pos.append(pos[6]+i)

# Define magnet strength factors (dependent on relative positions and time)
len1 = pos[2] - pos[1]
len2 = pos[4] - pos[2]
str = np.array([1, 1 + float(len1)/float(len2), 2*float(len1)/float(len2), 1 + float(len1)/float(len2), 1])

def strength(t):
    kick = str*np.array([
        np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
        1, -(np.sin(t*np.pi/100 + np.pi) + 1), 
        np.sin(t*np.pi/100 + np.pi) + 1
        ])
    return kick

# Define path through magnet
def get_elements(t):
    kick = strength(t)
    path = [
        Drifting(length[0]),Kicker(kick[0]),
        Drifting(length[1]),Kicker(kick[1]),
        Drifting(length[2]),InsertionDevice(),
        Drifting(length[3]),Kicker(kick[2]),
        Drifting(length[4]),InsertionDevice(),
        Drifting(length[5]),Kicker(kick[3]),
        Drifting(length[6]),Kicker(kick[4]),
        Drifting(length[7])
        ]
    return path


# Send electron vector through chicane magnets at time t.
def timestep(t):

    # Initialise electron beam and position within system
    e_beam = np.array([0,0])
    e_pos = [e_beam[0]]
#    # Initialise photon beam and position within system
    p_beam = []
#    sp = []

    path = get_elements(t)
    # Calculate positions of electron beam, photon beam, kickers and insertion devices.
    for p in range(len(path)):
        e_beam = path[p].increment(e_beam)
        if path[p].type() == 'drift':
            e_pos.append(e_beam[0])
        if path[p].type() == 'id':
            p_beam.append(e_beam[0])
        if path[p-2].type() == 'id':
            p_beam.append(e_beam[0])





    return e_pos, p_beam

def photon(t):
    p_beam = timestep(t)[1]
    px1 = p1_pos
    px2 = p2_pos
    py1 = p_beam[:len(p_beam)/2]
    py2 = p_beam[len(p_beam)/2:]
    grad1 = (py1[1]-py1[0])/(px1[1]-px1[0])
    grad2 = (py2[1]-py2[0])/(px2[1]-px2[0])
    for p in np.arange(1,9):
        py1.append(grad1*(px1[p]-px1[p-1])+py1[p-1])
        py2.append(grad2*(px2[p]-px2[p-1])+py2[p-1])
    return py1, py2







# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, sum(length)), ylim=(-2, 5))
e_line, = ax.plot([], [], lw=1)
idwhere, = ax.plot([], [], 'r.')
p_beam, = ax.plot([], [], 'r.')
'''
p_line, = ax.plot([], [], 'r-')
p_line2, = ax.plot([], [], 'r-')
'''

# Initialisation function: plot the background of each frame.
def init():

    e_line.set_data([], [])
    idwhere.set_data([], [])
    p_beam.set_data([], [])
    '''
    p_line.set_data([],[])
    p_line2.set_data([],[])
    '''
    return e_line, idwhere, p_beam, #p_line, p_line2,

import gc  # This can't stay here! This is garbage collection
# Animation function
def animate(t):
    e_data = timestep(t)
    p_data = photon(t)
    e_line.set_data(pos, e_data[0])
    idwhere.set_data(id_pos, [0,0])
    k1 = plt.axvline(x=kicker_pos[0], color='k', linestyle='dashed')
    k2 = plt.axvline(x=kicker_pos[1], color='k', linestyle='dashed')
    k3 = plt.axvline(x=kicker_pos[2], color='k', linestyle='dashed')
    k4 = plt.axvline(x=kicker_pos[3], color='k', linestyle='dashed')
    k5 = plt.axvline(x=kicker_pos[4], color='k', linestyle='dashed') # Must be a nicer way...
    '''
    p_line.set_data(data[4], data[5])
    p_line2.set_data(data[6], data[7])
    '''
    p_beam.set_data(p1_pos,p_data[0])
    k = [k1, k2, k3, k4, k5]
    gc.collect(0)
    return e_line, idwhere, k1, k2, k3, k4, k5, p_beam #p_line, p_line2,

# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

plt.show()




