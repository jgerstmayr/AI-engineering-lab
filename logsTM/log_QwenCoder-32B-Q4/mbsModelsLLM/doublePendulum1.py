# ** given model description: **
# Double pendulum system consisting of two mass points which are connected
# with inextensible strings with the following properties: mass m1 = 2 kg, mass
# m2 = 0.75 kg, length of the strings L1 = 1.25 m, L2 = 1.2 m, and gravity g
# = 11.15 m/s^2 which acts in negative y-direction. The first arm of the pendulum
# points in positive x direction and the second arm in positive y-direction. The
# strings are massless, inelastic and the length shall be constrained. Air resistance
# is neglected.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a point mass object with specified mass at reference position with optional initial conditions
oMass1 = mbs.CreateMassPoint(physicsMass=2, referencePosition=[1.25,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,-11.15,0])          

oMass2 = mbs.CreateMassPoint(physicsMass=0.75, referencePosition=[1.25,1.2,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,-11.15,0])          

#Create a rigid distance constraint between two points on different bodies or between a body and the ground.
oDistance1 = mbs.CreateDistanceConstraint(bodyNumbers=[oGround, oMass1], 
                                         localPosition0 = [0,0,0], 
                                         localPosition1 = [0,0,0], 
                                         distance=1.25)

oDistance2 = mbs.CreateDistanceConstraint(bodyNumbers=[oMass1, oMass2], 
                                         localPosition0 = [0,0,0], 
                                         localPosition1 = [0,0,0], 
                                         distance=1.2)

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
SC.visualizationSettings.nodes.tiling = 32


#start solver:
mbs.SolveDynamic(simulationSettings)


