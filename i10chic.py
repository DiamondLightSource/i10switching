# i10chic.py
# Animated simulation of chicane magnets

# Import libraries

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# Define matrices to modify the electron beam vector:
# drift, kicker magnets, insertion devices.


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
length = [2,1,8,6,4,9,3,7] # lengths to drift between kickers and IDs
pos = [0]
pos.extend(np.cumsum(length))

# Positions of kickers, IDs and 'on axis' photon beam points for plotting purposes.
kicker_pos = [pos[1],pos[2],pos[4],pos[6],pos[7]]
id_pos = [pos[3],pos[5]]
p_pos = [[pos[3], pos[3]+30],[pos[5],pos[5]+30]]

# Define magnet strength factors (dependent on relative positions and time)
len1 = pos[2] - pos[1]
len2 = pos[4] - pos[2]
d12 = float(len1)/float(len2)
len3 = pos[6] - pos[4]
len4 = pos[7] - pos[6]
d34 = float(len3)/float(len4)
stren = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34])

def strength(t):

    kick = stren*np.array([
        np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
        1, np.sin(t*np.pi/100) - 1,
        -np.sin(t*np.pi/100) + 1
        ])

    return kick
'''
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
'''
path = [
    Drifting(length[0]),Kicker(0),
    Drifting(length[1]),Kicker(1),
    Drifting(length[2]),InsertionDevice(),
    Drifting(length[3]),Kicker(2),
    Drifting(length[4]),InsertionDevice(),
    Drifting(length[5]),Kicker(3),
    Drifting(length[6]),Kicker(4),
    Drifting(length[7])
    ]



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

# Photon beam data: returns list of beam vector positions and velocity directions
def photon(t):

    photon_beam = timestep(t)[1]
    for vector in photon_beam:
        vector.extend(Drifting(p_pos[0][1]-p_pos[0][0]).increment(vector))

    return photon_beam

# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, sum(length)), ylim=(-2, 5))
e_line, = ax.plot([], [], lw=1)
p_beam1, = ax.plot([], [], 'r-')
p_beam2, = ax.plot([], [], 'r-')

# Initialisation function: plot the background of each frame.
def init():

    e_line.set_data([], [])
    p_beam1.set_data([], [])
    p_beam2.set_data([], [])
    
    return e_line, p_beam1, p_beam2,

import gc  # This can't stay here! This is garbage collection
# Animation function
def animate(t):
    e_data = timestep(t)[2] # NEEDS SORTING OUT
    p_data = photon(t)
    e_line.set_data(pos, e_data)
    p_beam1.set_data(p_pos[0],[p_data[0][0],p_data[0][2]])
    p_beam2.set_data(p_pos[1],[p_data[1][0],p_data[1][2]]) # I'm resetting the data each time but not sure I can do a multiple plot thing with the way the photon data is currently set up...
    gc.collect(0)
    return e_line, p_beam1, p_beam2,

# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

# Plot positions of kickers and IDs
for i in kicker_pos:
    plt.axvline(x=i, color='k', linestyle='dashed')
plt.plot(id_pos, [0,0], 'r.')


plt.show()


