#matrices

import dls_packages
import numpy as np


#temporary numbers
#k = strength of kicker --> amount by which velocity is incremented by kick
#dt = time increment of whole process
#ds = increment for electron vector
#a = 1 + k/x'
ds = 3

#initial position and velocity (along x axis)
e0 = np.array([1,0])


#allow electron to drift between magnets
drift = np.array([[1,ds],
		  [0,1]]) #this matrix is probably wrong way up to work with dot product - to sort

#k is the strength of the magnet and is equal to the CHANGE in velocity so v goes to v+k


def dipole(k,e):
	rotate = np.array([[np.cos(k), -np.sin(k)],
			   [np.sin(k), np.cos(k)]])
	return np.dot(rotate,e)

def convertfwd(e):
	return e[0]*np.array([np.cos(e[1]), np.sin(e[1])]) #have I got columns vs rows right?

def convertbck(e):
	return np.array([np.sqrt(e[0]**2+e[1]**2), np.arctan(e[1]/e[0])])

#apply dipole magnet to electron vector

k = np.pi/6
fwd = convertfwd(e0)
dipole = dipole(k,e0)
bck = convertbck(dipole)
#check = convertbck(fwd)

print e0[0]



#convert (x,v) to x(cosv,sinv)
#magnet.dipole(e)


'''
#initialise time step
t0 = 0

while True:

	dt = t0%100

	#strength k of magnet varies by sin function
	k = np.sin(dt*np.pi/50)

	if dt == 0:
		e = e0

	#apply dipole magnet test
	e = magnet(1+k/e(1))
'''
