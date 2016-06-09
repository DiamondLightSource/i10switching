# i10chic.py
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
length = [2,2,6,6,6,6,2,2] # lengths to drift between kickers and ids, currently must be symmetric about centre magnet
p = 0
pos = [p]
for L in length:
    p += L
    pos.append(p)
# Positions of kickers, ids, on axis photon beam points
kicker_pos = [pos[1],pos[2],pos[4],pos[6],pos[7]]
id_pos = [pos[3],pos[5]] #is there a nicer way of doing this?
p_pos = [[pos[3], pos[3]+30],[pos[5],pos[5]+30]]

# Define magnet strength factors (dependent on relative positions and time)
len1 = pos[2] - pos[1]
len2 = pos[4] - pos[2]
stren = np.array([1, 1 + float(len1)/float(len2), 2*float(len1)/float(len2), 1 + float(len1)/float(len2), 1]) # it's actually more complicated than this


def strength(t):

    kick = stren*np.array([
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

    return path #THIS SHOULDN'T BE IN A FUNCTION AND KICKER STRENGTHS SHOULDN'T BE TIME DEPENDENT HERE - NEEDS SORTING


# Send electron vector through chicane magnets at time t.
def timestep(t):

    # Initialise electron beam
    e_beam = np.array([0,0])
    e_loc = [e_beam[0]]
    e_vector = [0,0] # this currently doesn't do anything - need to work out how to use
    # Initialise photon beam
    p_vector = []

    path = get_elements(t)
    # Calculate positions of electron beam and photon beam relative to main axis
    for p in range(len(path)):
        e_beam = path[p].increment(e_beam)
        if path[p].type() == 'drift':
            e_loc.append(e_beam[0])
            e_vector.append([e_beam[0],e_beam[1]]) #must be a nicer way to append this data...
        if path[p].type() == 'id':
            p_vector.append([e_beam[0],e_beam[1]])

    return e_vector, p_vector, e_loc  # returns positions and locations but currently just using positions
'''
#columns testing
f = np.array(timestep(3)[1])
print f
print f[:,0]
print f[:,0][0]
'''

def photon(t):

    p1 = timestep(t)[1][0]
    p2 = timestep(t)[1][1]
    p1loc = [p1[0]]
    p2loc = [p2[0]]
    p1 = Drifting(p_pos[0][1]-p_pos[0][0]).increment(p1)
    p2 = Drifting(p_pos[1][1]-p_pos[1][0]).increment(p2)
    p1loc.append(p1[0])
    p2loc.append(p2[0])

    return p1loc, p2loc #should be able to combine this into a list so I don't have to repeat all the commands


# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, sum(length)), ylim=(-2, 5))
e_line, = ax.plot([], [], lw=1)
idwhere, = ax.plot([], [], 'r.')
p_beam1, = ax.plot([], [], 'r-')
p_beam2, = ax.plot([], [], 'r-')


# Initialisation function: plot the background of each frame.
def init():

    e_line.set_data([], [])
    idwhere.set_data([], [])
    p_beam1.set_data([], [])
    p_beam2.set_data([], [])

    return e_line, idwhere, p_beam1, p_beam2,


import gc  # This can't stay here! This is garbage collection
# Animation function
def animate(t):
    e_data = timestep(t)[2] # NEEDS SORTING OUT
    p_data = photon(t)
    e_line.set_data(pos, e_data)
    idwhere.set_data(id_pos, [0,0])
    k1 = plt.axvline(x=kicker_pos[0], color='k', linestyle='dashed')
    k2 = plt.axvline(x=kicker_pos[1], color='k', linestyle='dashed')
    k3 = plt.axvline(x=kicker_pos[2], color='k', linestyle='dashed')
    k4 = plt.axvline(x=kicker_pos[3], color='k', linestyle='dashed')
    k5 = plt.axvline(x=kicker_pos[4], color='k', linestyle='dashed') # Must be a nicer way...
    p_beam1.set_data(p_pos[0],p_data[0])
    p_beam2.set_data(p_pos[1],p_data[1])

    gc.collect(0)
    return e_line, idwhere, k1, k2, k3, k4, k5, p_beam1, p_beam2,


# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

plt.show()




