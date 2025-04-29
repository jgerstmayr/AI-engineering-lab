# ** given model description: **
# Projectile motion of a point mass with the following properties: mass m
# = 7.5 kg, gravity g = 11.15 m/s^2, initial velocity in x/y/z-direction: vx
# = 0.075 m/s, vy = 12.5 m/s, vz = 0 m/s. The initial position is given as
# x=0 and y=0. Gravity acts along the negative y-axis, and there is no other
# external propulsion or resistance. The motion shall be evaluated for 1 s. Contact
# with ground is not modelled, so the projectile can go below y=0. Except the
# action of gravity, no forces act on the point mass.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
#Create a ground object at given (optional) referencePosition.  Even several ground objects at specific positions can be added.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a point mass object with specified mass at reference position with optional initial conditions
#physicsMass: the mass in kg
#referencePosition: initial/reference position at which mechanism is defined; 
#initialDisplacement: additional initial deviations from referencePosition; usually this is [0,0,0]
#initialVelocity: initial velocities of mass point
#all vectors always have 3 components, no matter if 2D or 3D problem
oMass = mbs.CreateMassPoint(physicsMass=7.5, referencePosition=[0,0,0], 
                            initialDisplacement=[0,0,0],  #optional, relative to reference position
                            initialVelocity=[0.075,12.5,0],    #optional
                            gravity=[0,-11.15,0])          #optional

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.1


#start solver:
mbs.SolveDynamic(simulationSettings)


