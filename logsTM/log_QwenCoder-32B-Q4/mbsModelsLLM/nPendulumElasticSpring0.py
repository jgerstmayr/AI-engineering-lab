# ** given model description: **
# Multibody n-pendulum system consisting of 4 point masses connected with
# spring-dampers with the following properties: masses m = 3 kg, lengths of single elastic
# strings l_single = 0.3 m, stiffness k = 1000 and damping d = 400 of strings, and
# gravity g = 3.73 m/s^2 which acts in negative y-direction. The pendulum starts
# from horizontal configuration, where all masses are aligned with the x-axis,
# the first mass located at x=0.3, with a spring-damper connected to ground.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create point masses and spring-dampers for the n-pendulum system
masses = []
spring_dampers = []

#First mass connected to ground
masses.append(mbs.CreateMassPoint(physicsMass=3, referencePosition=[0.3,0,0], 
                                  initialDisplacement=[0,0,0], 
                                  initialVelocity=[0,0,0], 
                                  gravity=[0,-3.73,0]))

#Create spring-damper between ground and first mass
spring_dampers.append(mbs.CreateSpringDamper(bodyNumbers=[oGround, masses[-1]], 
                                            localPosition0=[0,0,0], 
                                            localPosition1=[0,0,0], 
                                            referenceLength=0.3, 
                                            stiffness=1000, damping=400))

#Additional masses and spring-dampers
for i in range(1, 4):
    masses.append(mbs.CreateMassPoint(physicsMass=3, referencePosition=[0.3 + i*0.3,0,0], 
                                      initialDisplacement=[0,0,0], 
                                      initialVelocity=[0,0,0], 
                                      gravity=[0,-3.73,0]))
    spring_dampers.append(mbs.CreateSpringDamper(bodyNumbers=[masses[-2], masses[-1]], 
                                                localPosition0=[0,0,0], 
                                                localPosition1=[0,0,0], 
                                                referenceLength=0.3, 
                                                stiffness=1000, damping=400))

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 0.5
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.06
SC.visualizationSettings.nodes.tiling = 16
SC.visualizationSettings.connectors.defaultSize = 0.02 #spring


#start solver:
mbs.SolveDynamic(simulationSettings)


