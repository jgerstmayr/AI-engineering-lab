# ** given model description: **
# Mass-spring-damper with the following properties: The mass point with mass
# m = 6 kg lies at [12 cm,0,0], stiffness k = 8000 N/m, and damping d = 20
# Ns/m. The force applied to the mass in x-direction is f = 5 N. The spring-damper
# between mass point and ground at [0,0,0] is aligned with the x-axis, the spring
# has a length of 12 cm and is initially relaxed. Gravity is neglected.
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
oMass = mbs.CreateMassPoint(physicsMass=6, referencePosition=[0.12,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])          

#Create a linear spring-damper system between two bodies or between a body and the ground.
oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.12, 
                                      stiffness=8000, damping=20)

#Applies a force in a specific direction to a point mass.
loadMassPoint = mbs.CreateForce(bodyNumber=oMass, loadVector=[5,0,0])

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
SC.visualizationSettings.nodes.defaultSize=0.01
SC.visualizationSettings.openGL.lineWidth = 3


#start solver:
mbs.SolveDynamic(simulationSettings)


