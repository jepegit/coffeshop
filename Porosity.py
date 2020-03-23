
"""
Created on Mon Mar 23 10:10:12 2020

@author: carlf
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

E = 3.6  # Potential in V (J/C or W/A) (average operating potential) for Si/ X full cell
Ec = 4  # potential in V for carbon / x full cell
# I=(C*L*0.001) # Areal capacity mAh/cm2
A = 1.767  # area of electrode in cm2
Th= 0.0006 # thickness in cm
L = [0.5, 1, 2]  # Loading in mg/cm2
C = 3579  # capacity in mAh/g or Ah/kg
Cc = 372  #
W = 0.000010  # total weight of all cell components in kg- Seperator/electrolyte/casings etc _THIS NEEDS TO HAVE REAL INPUT VALUES
n = 22  # electrons transferred
z = 5  # amount of Si in the alloy
Mw = 28  # Molecular weight of Si g/mol
F = 96485  # Faradays constant C/mol
QtheoSi = (1000 * n * F) / (3600 * Mw * z)  # convert from A to mA and s to h so the units will be [mAh/g]
QtheoCarbon = (1000 * F) / (3600 * 12 * 6)  # convert from A to mA and s to h so the units will be [mAh/g]

QSnO2 = (1000 * F * 4.4) / (3600 * 150.7)  # convert from A to mA and s to h so the units will be [mAh/g]
QSnO = (1000 * F * 4.4) / (3600 * 134.7)  # convert from A to mA and s to h so the units will be [mAh/g]

U = E * C  # energy density Silicon  W/kg based on cathode/anode weight
U2 = Ec * Cc  # energy density Carbon W/kg based on cathode/anode weight
Cut = 0.9  # carbon utilization

RSi = 0.3  # ratio Silicon
Rc = 1 - RSi  # ratio Carbon

Usi = (U * 0.000001 * A) / W  # Energy density in Wh/kg per actual cell weight Silicon
Uc = (U2 * 0.000001 * A) / W  # Energy density in Wh/kg per actual cell weight Carbon


#composite electrode with 60% Si, 15 binder, 15 % C black, 10 % Graphite
CB=0.15
Bind=0.15
Siut = 0.6  # silicon utilization
Gr=0.1 # graphite
# densities (from JP)
rho_si = 2.329           # g/ccm
rho_graphite = 2.1       # g/ccm
rho_CB= 2                  # g/ccm Or is this = dead material
rho_dead = 1.8           # g/ccm

Mass=0.0001257 #electrode material masse in g
Vt=A*Th # total volume of electrode cm3


Dens= CB*rho_CB+Bind*rho_dead+Siut*rho_si+Gr*rho_graphite

Vv=Mass/Dens          #volume electrode material
Porosity=(Vt-Vv)/Vt
### reference Theoretical Limits of Energy Density in Silicon-Carbon Composite Anode Based Lithium Ion Batteries
wsi = 0.05 # weight % Si
wc  = 0.9 # weight % Carbon
wb  = 0.05 # weight % binder
wcc  = 0 # weight % carbon black /conductive carbon
ssi=3600
sc=330
psi= 2.3 # density g/cc
pc= 2.24
pb=1.1
pcc=2


vsi1=(wsi/psi)/((wsi/psi)+(wc/pc)+(wb/pb)+(wcc/pcc)) #volume fraction Si ?
vc1=(wc/pc)/((wsi/psi)+(wc/pc)+(wb/pb)+(wcc/pcc)) #volume fraction C ?

PAL=0 # if we assume complete expansion into pores upon lithiation
PA = (((vsi1*280)+(vc1*10))/100)+PAL  # porosity of unlithiated Si/C
Pa = (100 -PA)/((wsi/psi)+(wc/pc)+(wb/pb)+(wcc/pcc))  #density anode g/volume
Ga=((wsi*ssi)+(sc*wc))/100 #gravimetric energy density anode mAh/g

#Va=Pa*Ga                   #volumetric capacity
Va=(100 -(((vsi1*280)+(vc1*10))/100)+PAL )/((wsi/psi)+(wc/pc)+(wb/pb)+(wcc/pcc))*(((wsi*ssi)+(sc*wc))/100 )
def f2(x):
    vsi = (x/ psi) / ((x / psi) + (wc / pc) + (wb / pb) + (wcc / pcc))  # volume fraction Si ?
    vc = (wc / pc) / ((x / psi) + (wc / pc) + (wb / pb) + (wcc / pcc))  # volume fraction C ?
    res = (100 -(((vsi*280)+(vc*10))/100)+PAL)/((x/psi)+(wc/pc)+(wb/pb)+(wcc/pcc))*(((x*ssi)+(sc*wc))/100 )

    ##
    # dens=(x* psi) + ((1-x-wb) * pc) + (wb * pb) + (wcc * pcc) # density g/ccc
    #PA1 = ((Vt)-((Mass/dens)*280*x))/((Vt))
   # Grav =((x*ssi)+(sc*wc))/100    #
   # Por= (((vsi*280)+(vc*10))/100)+PAL
    #Pa1 = (100 - PA1) / ((wsi / psi) + (wc / pc) + (wb / pb) + (wcc / pcc))
    #res = ((100-((x*2.8)+((100-wb-wc-x)*0.1)+PAL))*((x*36)+((100-wb-wcc-x)*3.3)))/((x/2.3)+((100-wb-wc-x)/2.24)+(wb/pb)+(wc/pc)) # paper retracted, used weight fraction, not volume fraction in eq for PA


    return res





#plot effect on thickess , loading on porosity
#Find effect of capacity vs volume increase vs porosity- from this estimate a starting porosity required to achive SET amount of capacity with a certain thickness

def f3(x):
    res = (A*((0.0067*x+0.02)*0.1)-((x*A*0.001)/Dens))/(A*((0.0067*x+0.02)*0.1))
    return res
# x*A*0.001 = Total volume, må se hvordan tykkelsen øker sfa loading for ekte prøver for å sette inn riktig y (thickness) = 0.0067x(loading) + 0.02 (in mm) /del på 10 for å få i cm
# Modell how volume change upon lithiation - how will this effect density and thickness

x = np.linspace(0, 100, 21)  # values between 0 to 1 , 11 values - Loading in mg/cm2
y = np.empty_like(x)  # define empty cell
y2 = np.empty_like(x)
y3 = np.empty_like(x)
y4 = np.empty_like(x)
# print(x)
i = 0
for xi in x:  # x=L
    #y[i] = f(xi)  # fill up empty cell calling on function f with imput L*i
    #y2[i] = f1(xi)
    y3[i] = f2(xi)
    y4[i] = f3(xi)
    i = i + 1


import matplotlib.pyplot as plt

plt.subplot(2, 1, 1)
#plt.figure(3)
plt.plot(x, y3, 'bx')
plt.title(['Volumetric capacity', RSi * 100])
plt.xlabel('Si wt %')
plt.ylabel('Volumetric capacity')

plt.subplot(2, 1, 2)
#plt.figure(4)
plt.plot(x, y4, 'bx')
plt.title(['Porosity/Loading', RSi * 100])
plt.xlabel('Loading [mg/cm2]')
plt.ylabel('Porosity')
plt.show()
#print(y)
#print(x)





