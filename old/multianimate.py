#attempts to do multiple animations as subplots

# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, sum(length)), ylim=(-2, 5))
beams = [plt.plot([], [])[0], plt.plot([], [], 'r')[0], plt.plot([], [], 'r')[0]]

# Initialisation function: plot the background of each frame.
def init():

    for line in beams:
        line.set_data([], [])
    
    return beams

import gc  # This can't stay here! This is garbage collection

# Animation function
def animate(t):
    # Obtain data for plotting.
    e_data = e_plot(t)
    p_data = p_plot(t)
    # Set data for electron beam.
    beams[0].set_data(pos, e_data)
    # Set data for two photon beams.
    for line, x, y in zip([beams[1],beams[2]], p_pos, p_data):
        line.set_data(x,y)

    gc.collect(0)

    return beams


# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

# Plot positions of kickers and IDs.
for i in kicker_pos:
    plt.axvline(x=i, color='k', linestyle='dashed')
for i in id_pos:
    plt.axvline(x=i, color='r', linestyle='dashed')


# Plot photon points at detector (actual number needs changing...)
# THIS WORKS FOR A SINGLE POINT IN TIME - HOW TO ANIMATE IT...
#subplot??
fig2 = plt.figure()
ax2 = plt.axes(xlim=(-10,10), ylim=(0, 5))

stuff = [plt.plot([], [])[0], plt.plot([], [], 'r')[0]]
#p_points = p_plot(2)[:,1]

def init2():

    for point in stuff:
        point.set_data([], [])
    
    return stuff


def ani(t):
    # Obtain data for plotting.
    p_data = p_plot(t)[:,1]
    # Set data for electron beam.
    stuff[0].set_data(t%100, p_data[0])
    stuff[1].set_data(t%100, p_data[1])



    return stuff
anim = animation.FuncAnimation(fig2, ani, init_func=init2,
                               frames=200, interval=10, blit=True)


#x = p_points
#y = [2%100,2%100]

#ax2.plot(x, y)



fig2 = plt.figure()
ax2 = plt.axes(xlim=(-10,10), ylim=(0,10))
points = ax2.plot([],[])[0]

def init2():
    points.set_data([],[])
    return points

def ani(t):
    p_points = p_plot(t)[:,1]
    points.set_data([p_points,t%100])
    return points

anim2 = animation.FuncAnimation(fig2, ani, init_func=init2, frames=200, interval=10, blit=True)



plt.show()


