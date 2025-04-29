# ** given model description: **
# A 3D mass point with mass m = 1.25 kg is attached to a string with length
# 0.75 m, with a predominant rotation around the z-axis due to centrifugal forces.
# Gravity g = 9.81 m/s^2 acts in negative z-direction. The mass point is placed initially
# at [0.75,0,0] and the initial velocity is [0,7.5,0], given in m/s. The elastic
# string shall be modelled as spring-damper with stiffness k = 2500 N/m and damping
# d = 30 Ns/m, which connects the mass point and the ground position at [0,0,0].
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
oMass = mbs.CreateMassPoint(physicsMass=1.25, referencePosition=[0.75,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,7.5,0],    
                            gravity=[0,0,-9.81])          

#Create a linear spring-damper system between two bodies or between a body and the ground.
oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.75, 
                                      stiffness=2500, damping=30)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 32


#start solver:
mbs.SolveDynamic(simulationSettings)


