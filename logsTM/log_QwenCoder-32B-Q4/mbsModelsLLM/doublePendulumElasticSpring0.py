# ** given model description: **
# Double pendulum consisting of two mass points which are connected with
# elastic springs with the following properties: mass m1 = 0.6 kg, mass m2 = 0.6
# kg, length of the strings L1 = 1.2 m, L2 = 0.5 m, stiffnesses k1 = 10000 and
# k2 = 2000, and gravity g = 3.73 m/s^2 which acts in negative y-direction.
# The first arm of the pendulum points in positive x-direction and the second
# arm in positive x-direction.
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
oMass1 = mbs.CreateMassPoint(physicsMass=0.6, referencePosition=[1.2,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,-3.73,0])          

oMass2 = mbs.CreateMassPoint(physicsMass=0.6, referencePosition=[1.2+0.5,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,-3.73,0])          

#Create a linear spring-damper system between two bodies or between a body and the ground.
oSpringDamper1 = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass1], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=1.2, 
                                      stiffness=10000, damping=0)

oSpringDamper2 = mbs.CreateSpringDamper(bodyNumbers=[oMass1, oMass2], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.5, 
                                      stiffness=2000, damping=0)

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
SC.visualizationSettings.nodes.defaultSize=0.1
SC.visualizationSettings.nodes.tiling = 32
SC.visualizationSettings.connectors.defaultSize = 0.05 #spring


#start solver:
mbs.SolveDynamic(simulationSettings)


