# ** given model description: **
# Multibody n-pendulum system consisting of 2 point masses with the following
# properties: masses m = 0.8 kg, length of inextensible strings l_single = 0.25 m, and
# gravity g = 9.81 m/s^2. The pendulum starts from horizontal configuration, where
# all masses are aligned along the x-axis (the first mass starting at x=0.25)
# and all masses have an initial velocity of 0.2 m/s in negative y-direction.
# Gravity acts in negative y-direction and air resistance is neglected. The strings
# between the consecutive masses (and the string between first mass and ground) shall
# be modelled as constrained distances.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create the first point mass object
oMass1 = mbs.CreateMassPoint(physicsMass=0.8, referencePosition=[0.25,0,0], 
                             initialDisplacement=[0,0,0],  
                             initialVelocity=[0,-0.2,0],    
                             gravity=[0,-9.81,0])

#Create the second point mass object
oMass2 = mbs.CreateMassPoint(physicsMass=0.8, referencePosition=[0.5,0,0], 
                             initialDisplacement=[0,0,0],  
                             initialVelocity=[0,-0.2,0],    
                             gravity=[0,-9.81,0])

#Create a rigid distance constraint between the ground and the first mass
oDistance1 = mbs.CreateDistanceConstraint(bodyNumbers=[oGround, oMass1], 
                                          localPosition0 = [0,0,0], 
                                          localPosition1 = [0,0,0], 
                                          distance=0.25)

#Create a rigid distance constraint between the first and the second mass
oDistance2 = mbs.CreateDistanceConstraint(bodyNumbers=[oMass1, oMass2], 
                                          localPosition0 = [0,0,0], 
                                          localPosition1 = [0,0,0], 
                                          distance=0.25)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 16


#start solver:
mbs.SolveDynamic(simulationSettings)


