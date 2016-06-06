#chicane1.py
#first attempt at recreating I10_chic.m in python

#import libraries
import dls_packages
import numpy as np
import matplotlib.pyplot as plt

#extent of simulation
x = (np.arange(-10,10)+1)

#magnet information: locations, strengths, polarisations
mloc = [-4, -3, 0, 3, 4]
mstr0 = np.array([1, 1.333, 0.333, 1.333, 1])
mpol = np.array([+1, -1, +1, -1, +1])

#initial electron velocity (first row forwards, second vertical)
eV0 = np.array([[0.5],
		[0]])


#initialise timestep
ts = 0


#run forever
while True:
	t = ts%4 #goes from 0 to 99 looping as ts increases

	#initialise electron beam position and velocity	
	if ts == 0:
		ePy = np.zeros(len(x))	#electron beam initially lies along x axis
		eVy = np.zeros(len(x))		#electron velocity vectors initially only point along x axis so y velocity = 0
	#at magnet locations apply kick to modify electron velocity vector in y direction
	indexes = []
	strengths = np.array([0,np.sin(t*np.pi/2),0,np.sin(t*np.pi/2 + np.pi/2),0])*mstr0	#not sure I've applied the correct waveform to the magnets...
	for i in range(len(x)):
		if x[i] in set(x).intersection(mloc):
			indexes.append(i)
	for (index, strength) in zip(indexes, strengths):
		eVy[index] += strength
	#increment position vector
	ePy += eVy #is this right? check... think about it...
	ts += 1

	plt.plot(x,ePy)
	plt.draw()
	plt.show()

#how to plot the electron beam correctly...


#the problem is that I think I need to plot a sin field with nodes at magnets 1, 3 and 5 that varies between 0 and max ie a standing wave for the magnets. I don't have that currently! And goodness knows what's happening with adding the strengths...

#test plots to remind myself how to do it
'''
plt.plot(np.arange(10),np.zeros(10))
plt.plot(np.zeros(10)-3,np.arange(10),'b--')
plt.show()
'''
