# ** given model description: **
# Two mass points connected by distance constraint. The mass points both
# have mass m1 = m2 = 0.8 kg, are initially located at p1 = [-0.3,0,0] and p2
# = [0.3,0,0], positions given in m. Mass m1 has initial velocity vy = 1 m/s
# and m2 has initial velocity vy = -1 m/s while all other initial velocity components
# are zero. No gravity nor forces are present.
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
oMass1 = mbs.CreateMassPoint(physicsMass=0.8, referencePosition=[-0.3,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,1,0],    
                            gravity=[0,0,0])

oMass2 = mbs.CreateMassPoint(physicsMass=0.8, referencePosition=[0.3,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,-1,0],    
                            gravity=[0,0,0])

#Create a rigid distance constraint between two points on different bodies or between a body and the ground.
oDistance = mbs.CreateDistanceConstraint(bodyNumbers=[oMass1, oMass2], 
                                         localPosition0 = [0,0,0], 
                                         localPosition1 = [0,0,0], 
                                         distance=None)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
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

