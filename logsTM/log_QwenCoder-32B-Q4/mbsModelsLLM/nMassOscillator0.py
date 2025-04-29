# ** given model description: **
# A serial chain of 4 masses connected with springs-dampers. Each mass has
# m = 12 kg, the stiffnesses are k = 5000 N/m, and the damping coefficients
# are d = 50 Ns/m. A force f = 50 N is applied to the last mass (with highest
# index). The first mass is connected to ground via the first spring-damper. The
# relaxed length of each spring is 0.3 m, and the first mass is located at z = 0.3
# m. The serial chain is oriented along the global z-axis. Gravity acts in positive
# z-direction, with g = 11.15 m/s^2.
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
oMass1 = mbs.CreateMassPoint(physicsMass=12, referencePosition=[0,0,0.3], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,11.15])          

oMass2 = mbs.CreateMassPoint(physicsMass=12, referencePosition=[0,0,0.6], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,11.15])          

oMass3 = mbs.CreateMassPoint(physicsMass=12, referencePosition=[0,0,0.9], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,11.15])          

oMass4 = mbs.CreateMassPoint(physicsMass=12, referencePosition=[0,0,1.2], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,11.15])          

#Create a linear spring-damper system between two bodies or between a body and the ground.
oSpringDamper1 = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass1], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.3, 
                                      stiffness=5000, damping=50)

oSpringDamper2 = mbs.CreateSpringDamper(bodyNumbers=[oMass1, oMass2], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.3, 
                                      stiffness=5000, damping=50)

oSpringDamper3 = mbs.CreateSpringDamper(bodyNumbers=[oMass2, oMass3], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.3, 
                                      stiffness=5000, damping=50)

oSpringDamper4 = mbs.CreateSpringDamper(bodyNumbers=[oMass3, oMass4], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.3, 
                                      stiffness=5000, damping=50)

#Applies a force in a specific direction to a point mass.
loadMassPoint = mbs.CreateForce(bodyNumber=oMass4, loadVector=[0,0,50])

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.1


#start solver:
mbs.SolveDynamic(simulationSettings)


