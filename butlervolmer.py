#
# This solves and plots the BV equation
#
import matplotlib.pyplot as plt
import numpy as np


R=8.3145 # Gas constant
F=96485 # Faraday constant
alpha=0.5 # charge transfer coeff
z=1 # nr of electrons
j0=1 # exchange current density
T=300 # Temperature

eta=np.linspace(-0.1,0.1,100) # overpotential

ja=j0*np.exp(alpha*z*F/(R*T)*eta)       # anodic current density
jn=-j0*np.exp(-(1-alpha)*z*F/(R*T)*eta) # cathodic current density
j=ja+jn                                 # total current density
plt.plot(eta,ja)
plt.plot(eta,jn)
plt.plot(eta,j)
plt.xlabel('Overpotential [V]')
plt.ylabel('Current Density [A/m$^2$]')
plt.legend(['$j_a$', '$j_n$', '$j$'], loc='upper left')
plt.show()