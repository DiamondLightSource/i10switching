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


    def __init__(self):
        pass
        #self.step = None

    def set_length(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

    def get_type(self):
        return 'drift'


class Kicker:


    def __init__(self):
        pass
        #self.k = None

    def set_strength(self, k):
        self.k = k

    def increment(self, e):
        kick = np.array([0, self.k])
        return e + kick

    def get_type(self):
        return 'kicker'


class InsertionDevice:


    def __init__(self):
        pass

    def increment(self, e):
        return e

    def get_type(self):
        return 'id'


# Define positions of stuff in system
length = [2,1,8,6,4,9,3,7] # lengths to drift between kickers and IDs
pos = [0]
pos.extend(np.cumsum(length))

# Positions of kickers, IDs and 'on axis' photon beam points for plotting purposes.
kicker_pos = [pos[1],pos[2],pos[4],pos[6],pos[7]]
id_pos = [pos[3],pos[5]]
p_pos = [[pos[3], pos[3]+30],[pos[5],pos[5]+30]]

# Define magnet strength factors (dependent on relative positions and time).
len1 = pos[2] - pos[1]
len2 = pos[4] - pos[2]
d12 = float(len1)/float(len2)
len3 = pos[6] - pos[4]
len4 = pos[7] - pos[6]
d34 = float(len3)/float(len4)
stren = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34])

def calculate_strengths(t):

    kick = stren*np.array([
        np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
        1, np.sin(t*np.pi/100) - 1,
        -np.sin(t*np.pi/100) + 1
        ])

    return kick

# Define path through system.
path = [
    Drifting(),Kicker(),
    Drifting(),Kicker(),
    Drifting(),InsertionDevice(),
    Drifting(),Kicker(),
    Drifting(),InsertionDevice(),
    Drifting(),Kicker(),
    Drifting(),Kicker(),
    Drifting()
    ]
#function that returns all items in order of particular type so don't have to check if it's a kicker when going through

def get_elements(path, which):
    objects = []
    for p in path:
        if p.get_type() == which:
            objects.append(p)
    return objects

#print get_elements(path, 'kicker')


#stuff so far: positions of kickers and ids in system, drift lengths, path with drifts and kicks
#aha what I want is just path[Drifting(),Kicker()...] and THEN know WHICH drift and kick applies from using get_elements somehow
#store the electron vector at each point, don't just need to update and then lose it...
#so you have the list of drifts as get_elements(path)[0] and you then have .increment(e_beam, length) where you call length from the list
#and for kickers you have get_elements(path)[1] and do .increment(e_beam, kick) where kick is called from list (and this is within time loop so kick is a list of particular values at any one time)
#for ids it's just get_elements(path)[2].increment(e_beam)
#so probably you want to set all those up and then call them in the correct order on e_beam, and only append to e_vector after drifts...
#so it's a function dependent on e_beam
'''
def do_the_thing(whatsit, kick, length):
    thingies = get_elements(path)
    actiondrift = []
    actionkick = []
    actionid = []
    for n in range(thingies[0]):
        actiondrift.append(thingies[0][n].increment(whatsit, length[n]))
    for k in range(thingies[1]):
        actionkick.append(thingies[1][k].increment(whatsit, kick[k]))
    for th in thingies[2]:
        actionid.append(th.increment(whatsit)
    return actiondrift, actionkick, actionid
'''
#i think what I actually want is separate do_the_things for do_the_drift etc which I can call on the devices from get_elements

# the problem is I want to call the elements in order...

# so I've got currently: [drift, kick, drift...] and then I've got [drift, drift, drift...] and [kick, kick...] but those aren't obviously identified by anything. Need to identify them by their position in path
# ie want [drift(0),drift(2)...] and [kick(1), kick(3)...] 
#can i make get_elements do that??

#so I have 3 commands to do to e_beam and I have to do them in the right order and with the right strengths and lengths
#path tells me the order in which to apply the commands to e_beam
#but it doesn't tell me what strength/length to apply (or shouldn't)
#I should be able to get from the position of the object in path to knowing what strength/length to apply
#so if I start with path[1] (which is a kicker and should have strength(t)[0]) I want to call a function on path[2] that finds out that it is a kicker and that it is the first kicker in the path so should have the first kick strength
#hence it returns path[1].increment(e_beam, strength(t)[0])
#whereas for path[2] it'll work out it's a drift and it's the second drift so it'll return path[2].increment(e_beam, length[1])
#HOWEVER to know that 



#have path then set strengths and lengths then loop through path







# Take path element, find out what element it is, apply relevant action

# Send electron vector through chicane magnets at time t.
def timestep(t):

    # Initialise electron beam
    e_beam = np.array([0,0])
    e_loc = [e_beam[0]]
    e_vector = [0,0] # this currently doesn't do anything - need to work out how to use

    # Initialise photon beam
    p_vector = []

    # Calculate positions of electron beam and photon beam relative to main axis
    for kicker, strength in zip(get_elements(path, 'kicker'), calculate_strengths(t)):
         kicker.set_strength(strength)
    for drift, dist in zip(get_elements(path, 'drift'), length):
         drift.set_length(dist)
    for p in path:
            e_beam = p.increment(e_beam)
            e_loc.append(e_beam[0])
            e_vector.append([e_beam[0],e_beam[1]])  # Allow electron vector to drift and append its new location and velocity to vector collecting the data #must be a nicer way to append this data...

#            p_vector.append([e_beam[0],e_beam[1]])  # Electron vector passes through insertion device, photon vector created
    
    return e_vector, p_vector, e_loc  # returns positions and locations but currently just using positions STILL NEEDS SOME TIDYING
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
    # Allow photon vector to drift over large distance (ie off the graph)
    # and add the vector describing its new position and velocity to the 
    # information of its original position. For both beams simultaneously.
    for vector in photon_beam:
        vector.extend(Drifting(p_pos[0][1]-p_pos[0][0]).increment(vector))

    return photon_beam

# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, sum(length)), ylim=(-2, 3))
e_line, = ax.plot([], [], lw=1)
#p_beam1, = ax.plot([], [], 'r-')
#p_beam2, = ax.plot([], [], 'r-')

# Initialisation function: plot the background of each frame.
def init():

    e_line.set_data([], [])
#    p_beam1.set_data([], [])
#    p_beam2.set_data([], [])
    
    return e_line, #p_beam1, p_beam2,

import gc  # This can't stay here! This is garbage collection

# Animation function
def animate(t):

    e_data = timestep(t)[2] # NEEDS SORTING OUT
    p_data = photon(t)
    e_line.set_data(np.arange(len(e_data)), e_data) # currently plotting against integers because e_data has excess values that I need to get rid of...
#    p_beam1.set_data(p_pos[0],[p_data[0][0],p_data[0][2]])
#    p_beam2.set_data(p_pos[1],[p_data[1][0],p_data[1][2]]) # I'm resetting the data each time but not sure I can do a multiple plot thing with the way the photon data is currently set up...
    gc.collect(0)

    return e_line, #p_beam1, p_beam2,

# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

# Plot positions of kickers and IDs
for i in kicker_pos:
    plt.axvline(x=i, color='k', linestyle='dashed')
plt.plot(id_pos, [0,0], 'r.')


plt.show()


