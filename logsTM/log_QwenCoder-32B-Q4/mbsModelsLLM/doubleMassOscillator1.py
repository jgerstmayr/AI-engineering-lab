# ** given model description: **
# Two-mass-spring-damper system consisting of two masses with the following
# properties: mass m1 = m2 = 12 kg, stiffness k1 = k2 = 7500 N/m, and damping d1 = d2
# = 12.5 Ns/m. The first mass is placed at [7.5 cm,0,0] and the second mass
# at [2*7.5 cm,0,0]. The first spring is connected to ground at [0,0,0], and
# the second spring connects the two masses. Each spring has a reference length
# of 7.5 cm and is relaxed in the initial configuration. A force 5 is applied
# in x-direction to mass 2. No gravity is applied to the system.
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
oMass1 = mbs.CreateMassPoint(physicsMass=12, referencePosition=[0.075,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])          

oMass2 = mbs.CreateMassPoint(physicsMass=12, referencePosition=[0.15,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])          

#Create a linear spring-damper system between two bodies or between a body and the ground.
oSpringDamper1 = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass1], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.075, 
                                      stiffness=7500, damping=12.5)

oSpringDamper2 = mbs.CreateSpringDamper(bodyNumbers=[oMass1, oMass2], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.075, 
                                      stiffness=7500, damping=12.5)

#Applies a force in a specific direction to a point mass.
loadMassPoint = mbs.CreateForce(bodyNumber=oMass2, loadVector=[5,0,0])

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
SC.visualizationSettings.nodes.defaultSize=0.015
SC.visualizationSettings.connectors.defaultSize=0.01

# pass
# pass

#start solver:
mbs.SolveDynamic(simulationSettings)

# pass
# pass

