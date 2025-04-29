# ** given model description: **
# Double pendulum consisting of two mass points which are connected with
# elastic springs with the following properties: mass m1 = 1 kg, mass m2 = 0.8 kg,
# length of the strings L1 = 1.5 m, L2 = 1.2 m, stiffnesses k1 = 3000 and k2 = 750,
# and gravity g = 3.73 m/s^2 which acts in negative y-direction. The first arm
# of the pendulum points in positive x-direction and the second arm in negative
# x-direction.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create the first mass point with specified mass at reference position
oMass1 = mbs.CreateMassPoint(physicsMass=1, referencePosition=[1.5,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,-3.73,0])          

#Create the second mass point with specified mass at reference position
oMass2 = mbs.CreateMassPoint(physicsMass=0.8, referencePosition=[1.5-1.2,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,-3.73,0])          

#Create a linear spring-damper system between the ground and the first mass point
oSpringDamper1 = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass1], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=1.5, 
                                      stiffness=3000, damping=0)

#Create a linear spring-damper system between the first and the second mass point
oSpringDamper2 = mbs.CreateSpringDamper(bodyNumbers=[oMass1, oMass2], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=1.2, 
                                      stiffness=750, damping=0)

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


