#matrices

import dls_packages
import numpy as np


#k = strength of kicker --> amount by which velocity is incremented by kick
#dt = time increment of whole process
#ds = increment for electron vector
ds = 3 #just given it a number for now

#initial position and velocity (along x axis)
e0 = np.array([0,0])

#allow electron to drift between magnets
class drift:
	def __init__(self,ds,e):
		self.ds = ds
		self.e = e

	def drift(ds, e):
		increment = np.array([[1,ds],
				      [0,1]])
		return np.dot(increment,e)

class kicker:
	def __init__(self,k,e):
		self.k = k
		self.e = e

	def dipole(k, e):
		kick = np.array([0, k])
		return e + kick

class ID:
	def __init__(self,e):
		self.e = e
	def where:
		return e

'''

	def dipole(k,e):
		rotate = np.array([[np.cos(k), -np.sin(k)],
				   [np.sin(k), np.cos(k)]])
		return np.dot(rotate,e)

#convert position/velocity vector into a form suitable for applying the dipole magnet to it, and convert back
class convert:
	def __init__(self,e):
		self.e = e
	def fwd(e):
		return e[0]*np.array([np.cos(e[1]), np.sin(e[1])])

	def bck(e):
		return np.array([np.sqrt(e[0]**2+e[1]**2), np.arctan(e[1]/e[0])])
'''
#apply dipole magnet to electron vector

k = np.pi/6
forwd = e0.convert
dipole = dipole(k,e0)
back = convert.bck(dipole)
#check = convertbck(fwd)

print drift(e0)



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
